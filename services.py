import re
from datetime import date,datetime,time,timedelta,timezone
from fastapi import HTTPException
from models import *

def clock(): return datetime.now(timezone(timedelta(hours=5,minutes=30))).replace(tzinfo=None)
def fail(msg,code=422): raise HTTPException(code,msg)
def require(condition,msg,code=422):
    if not condition: fail(msg,code)
def get(db,cls,id):
    obj=db.get(cls,int(id))
    if not obj: fail("Record unavailable.",404)
    return obj
def email(value):
    value=value.strip().lower()
    require(len(value)<=254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value),"Enter a valid email.")
    return value
def adult_on(dob):
    try: return dob.replace(year=dob.year+18)
    except ValueError: return dob.replace(year=dob.year+18,day=28)
def effective(m,day=None):
    if isinstance(m,dict): return m.get("tier","Free")
    day=day or clock().date()
    if not m or not m.expiry or m.expiry<day or (m.tier=="Junior" and adult_on(m.dob)<=day): return "Free"
    return m.tier
def membership_status(m):
    if m.tier=="Free": return "Active"
    if effective(m)=="Free": return "Expired"
    return "Expiring Soon" if (m.expiry-clock().date()).days<=7 else "Active"
def rate(m,dept,day=None):
    rates={"Courts":{"Gold":100,"Silver":50,"Junior":30},"Shop":{"Gold":15,"Silver":10,"Junior":5},"Bar":{"Gold":15,"Silver":10,"Junior":5}}
    return rates.get(dept,{}).get(effective(m,day),0)
def sale(db,u,m,dept,mode,status="Paid",**kw):
    require(mode in ("Cash","Card","UPI","Included","Pending"),"Invalid payment method")
    s=Sale(actor_id=u.id,member_id=m.id if m else None,department=dept,mode=mode,status=status,created=clock(),settled=clock() if status=="Paid" else None,**kw)
    db.add(s); db.flush()
    return s
def line(db,s,name,price,qty=1,pct=0,product=None,ticket="",batch=0):
    gross=price*qty
    discount=(gross*pct+50)//100
    db.add(Item(sale_id=s.id,name=name,product_id=product.id if product else None,qty=qty,price=price,discount=discount,total=gross-discount,ticket=ticket,batch=batch))
    s.total+=gross-discount; s.discount+=discount
    if product: s.cost+=product.cost*qty
def slot(c,start):
    end=start+timedelta(hours=1)
    if start.second or start.microsecond or start.minute not in (0,30) or start.hour<6 or end.time()>time(22) or start.hour>=22: return "Closed"
    if c.social and start.weekday()==4 and start.time()<time(20) and end.time()>time(18):
        return "Social" if start.hour in (18,19) and start.minute==0 else "Closed"
    return "Private"
def book(db,u,m,c,start,mode,status="Booked"):
    require(clock()<start<clock()+timedelta(days=91),"Select a future slot within 90 days.")
    kind=slot(c,start); require(kind!="Closed","Outside playable hours or overlaps Friday social.")
    end=start+timedelta(hours=1)
    active=db.query(Booking).filter(Booking.status.in_(["Booked","Pending"]))
    midnight=datetime.combine(start.date(),time())
    require(active.filter(Booking.member_id==m.id,Booking.start>=midnight,Booking.start<midnight+timedelta(days=1)).count()<2,"Daily limit of two sessions reached.",409)
    overlaps=active.filter(Booking.start<end,Booking.end>start)
    require(not overlaps.filter_by(member_id=m.id).first(),"Member already has an overlapping session.",409)
    taken=overlaps.filter_by(court_id=c.id).all()
    require(not taken or (kind=="Social" and len(taken)<8 and all(b.is_social and b.start==start for b in taken)),"Court or social session is full.",409)
    pct=100 if kind=="Social" else rate(m,"Courts",start.date())
    s=sale(db,u,m,"Courts","Included" if pct==100 else mode,status="Paid" if status=="Booked" else "Pending")
    line(db,s,c.name+" · "+kind,c.price,pct=pct)
    b=Booking(court_id=c.id,member_id=m.id,start=start,end=end,is_social=kind=="Social",sale_id=s.id,status=status)
    db.add(b); db.flush()
    return b
def products(db,s,m,dept,cart,batch=0):
    require(isinstance(cart,list) and 0<len(cart)<=100,"Add at least one item.")
    for row in cart:
        p=get(db,Product,row["id"]); q=int(row["qty"])
        require(1<=q<=999 and p.department==dept,"Invalid item or quantity.")
        require(p.stock_on_hand>=q,p.name+" has insufficient stock.",409)
        p.stock_on_hand-=q
        line(db,s,p.name,p.price,q,rate(m,dept),p,"New" if dept=="Bar" else "",batch)

def inventory_health(db, dept="Shop"):
    ps = db.query(Product).filter_by(department=dept).all()
    total_val = sum(p.price * p.stock_on_hand for p in ps)
    total_cost = sum(p.cost * p.stock_on_hand for p in ps)
    low_stock = [p for p in ps if 0 < p.stock_on_hand <= p.reorder_level]
    out_of_stock = [p for p in ps if p.stock_on_hand <= 0]
    cats = {}
    for p in ps:
        cats[p.category] = cats.get(p.category, 0) + p.stock_on_hand
    return {
        "total_products": len(ps),
        "total_valuation": total_val,
        "total_cost": total_cost,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "categories": cats,
        "low_stock_items": [{"id": p.id, "name": p.name, "category": p.category, "stock": p.stock_on_hand, "reorder": p.reorder_level} for p in low_stock[:10]]
    }

def compute_lead_score(lead):
    score = 10
    if lead.status == "Online": score += 40
    score += min(30, (lead.total_connections or 0) * 2)
    try:
        mb = float(lead.data_used_mb or 0)
        score += min(20, int(mb / 100))
    except (ValueError, TypeError): pass
    if lead.trial: score += 25
    return min(100, score)

def crm_telemetry_metrics(db):
    leads = db.query(Lead).all()
    now_dt = clock()
    six_h_cutoff = now_dt - timedelta(hours=6)
    
    total = len(leads)
    online_count = 0
    recent_6h = 0
    total_data_mb = 0.0
    cities = {}
    protocols = {}
    stages = {"New": 0, "Contacted": 0, "Quote Sent": 0, "Converted": 0}

    for l in leads:
        if l.status == "Online": online_count += 1
        if l.created and l.created >= six_h_cutoff: recent_6h += 1
        if l.city: cities[l.city] = cities.get(l.city, 0) + 1
        if l.protocol: protocols[l.protocol] = protocols.get(l.protocol, 0) + 1
        if l.stage in stages: stages[l.stage] += 1
        try: total_data_mb += float(l.data_used_mb or 0)
        except (ValueError, TypeError): pass

    top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "total_inquiries": total,
        "online_now": online_count,
        "connected_last_6h": recent_6h,
        "total_bandwidth_gb": round(total_data_mb / 1024, 2),
        "top_cities": top_cities,
        "protocols": protocols,
        "pipeline_stages": stages
    }
