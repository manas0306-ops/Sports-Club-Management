import csv,io,os,secrets
from pathlib import Path
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from services import *
from database import Session,engine
from security import sign,unsign,digest,password_hash,password_ok
from seed import seed

app=FastAPI(title="The Champions Club",docs_url=None,redoc_url=None,openapi_url=None)
root=Path(__file__).resolve().parent
tpl=Jinja2Templates(directory=str(root/"templates"))
app.mount("/static",StaticFiles(directory=str(root/"static")),name="static")
seed()
def database(req:Request):
    with Session() as db:
        if req.method=="POST":
            require(req.headers.get("x-club-request")=="1","Request verification failed",403)
            if engine.dialect.name=="sqlite": db.execute(text("BEGIN IMMEDIATE"))
            else: db.execute(text("SELECT pg_advisory_xact_lock(7815601)"))
        yield db

def current(req,db):
    token=unsign(req.cookies.get("club",""))
    try: uid,nonce=token.split(":"); u=db.get(User,int(uid))
    except (ValueError,TypeError): return None
    return u if u and u.active and any(x["h"]==digest(nonce) and x["exp"]>clock().isoformat() for x in u.sessions) else None
def check(req,db,roles):
    u=current(req,db)
    require(u and (u.role in roles or u.role=="owner"),"Forbidden",403)
    return u
def member(db,u): return db.query(Member).filter_by(user_id=u.id).first()
def template(req,name,**kw):
    return tpl.TemplateResponse(request=req,name=name+".html",context=kw)
def period_start(period):
    day=clock().date()
    return {"today":day,"week":day-timedelta(days=day.weekday()),"month":day.replace(day=1)}.get(period,day)
def money(v): return "₹"+format(v/100,",.2f")
tpl.env.filters["money"]=money
tpl.env.globals.update(effective=effective,membership_status=membership_status,now=clock)
def name_for(db,m): return get(db,User,m.user_id).name
def add_user(db,data,role):
    addr=email(data["email"]); name=data["name"].strip(); pw=data["password"]
    require(name and 8<=len(pw.encode())<=72,"Name and an 8–72 byte password required.")
    require(not db.query(User).filter_by(email=addr).first(),"Email already registered.",409)
    u=User(name=name,email=addr,password=password_hash(pw),role=role)
    db.add(u); db.flush()
    if role=="member":
        dob=date.fromisoformat(data["dob"]); require(date(1900,1,1)<=dob<=clock().date(),"Invalid DOB")
        db.add(Member(user_id=u.id,dob=dob))
    return u

@app.get("/")
def home(req:Request,db=Depends(database)):
    return template(req,"index",user=current(req,db),courts=db.query(Court).all(),gear=db.query(Product).filter_by(department="Shop").all())
@app.get("/login")
def login(req:Request): return template(req,"login",user=None)
@app.get("/api/availability")
def availability(day:date,sport:str="",kind:str="",db=Depends(database)):
    courts=db.query(Court).all(); output=[]
    require(abs((day-clock().date()).days)<=92,"Date outside calendar")
    for c in courts:
        if sport and sport!=c.sport or kind and kind!=c.kind: continue
        rows=db.query(Booking).filter_by(court_id=c.id,status="Booked").filter(Booking.start>=datetime.combine(day,time()),Booking.start<datetime.combine(day+timedelta(days=1),time())).all()
        times=[]
        for half in range(12,43):
            t=datetime.combine(day,time(half//2,30*(half%2))); k=slot(c,t)
            occupied=sum(b.start<t+timedelta(hours=1) and b.end>t for b in rows)
            times.append(dict(start=t.isoformat(timespec="minutes"),kind=k,left=max(0,(8 if k=="Social" else 1)-occupied) if k!="Closed" and t>clock() else 0))
        output.append(dict(id=c.id,name=c.name,kind=c.kind,price=c.price,slots=times))
    return output
@app.get("/dashboard")
def dash(req:Request,period:str="today",day:date|None=None,db=Depends(database)):
    u=current(req,db)
    if not u:return RedirectResponse("/login",303)
    role=u.role; m=member(db,u); today=clock().date(); day=day or today
    data=dict(user=u,m=m,today=today,day=day,period=period)
    if role in ("member","desk","owner"):
        data["courts"]=db.query(Court).all()
        bookings=db.query(Booking).order_by(Booking.start.desc())
        data["bookings"]=(bookings.filter_by(member_id=m.id) if m else bookings).all()
    if role in ("desk","shop","bar","owner"):
        data["members"]=[dict(id=x.id,name=name_for(db,x),tier=effective(x),expiry=x.expiry) for x in db.query(Member).join(User).filter(User.active==True)]
    if role in ("member","physio","owner"):
        data["physios"]=db.query(User).filter_by(role="physio",active=True).all()
        q=db.query(Appointment)
        if m:q=q.filter_by(member_id=m.id)
        if role=="physio":q=q.filter_by(staff_id=u.id).filter(Appointment.start>=datetime.combine(day,time()),Appointment.start<datetime.combine(day+timedelta(days=1),time()))
        data["appointments"]=q.order_by(Appointment.start).all()
    if role in ("desk","owner"):data["leads"]=db.query(Lead).order_by(Lead.id.desc()).all()
    if role in ("bar","shop","member","owner"):
        ps=db.query(Product)
        if role in ("shop","bar"):ps=ps.filter_by(department=role.title())
        data["products"]=ps.all()
    if role in ("bar","owner"):
        data["shifts"]=db.query(Shift).order_by(Shift.id.desc()).all()
        data["tabs"]=db.query(Sale).filter_by(department="Bar",status="Open").all()
        data["bar_orders"]={s.id:s for s in db.query(Sale).filter_by(department="Bar")}
        data["tickets"]=db.query(Item).join(Sale).filter(Sale.department=="Bar",Item.ticket.in_(["New","Preparing","Ready"])).order_by(Item.id).all()
    sales=db.query(Sale).order_by(Sale.id.desc())
    if role=="member":sales=sales.filter_by(member_id=m.id)
    elif role!="owner":sales=sales.filter(Sale.department.in_({"desk":["Courts","Memberships"],"physio":["Physio"],"bar":["Bar"],"shop":["Shop"]}[role]))
    if role=="physio":sales=sales.filter(Sale.id.in_(db.query(Appointment.sale_id).filter_by(staff_id=u.id)))
    data["sales"]=sales.all()
    if role=="owner":
        data.update(profiles={v.user_id:v for v in db.query(Member)},users=db.query(User).all(),leaves=db.query(Leave).all(),payroll=db.query(Payroll).all(),stats=stats(db,period))
    if role not in ("owner","member"):
        data["my_leaves"]=db.query(Leave).filter_by(staff_id=u.id).all()
    return template(req,"admin" if role=="owner" else role,**data)

def stats(db,period):
    since=datetime.combine(period_start(period),time()); rows=db.query(Sale).filter(Sale.status=="Paid",Sale.settled>=since,Sale.settled<=clock()).all()
    depts={k:0 for k in ["Courts","Shop","Bar","Physio","Memberships","B2B"]}; modes={k:0 for k in ["Cash","Card","UPI"]}
    for s in rows:
        depts[s.department]+=s.total-s.tax
        if s.mode in modes:modes[s.mode]+=s.total
    return dict(departments=depts,modes=modes,revenue=sum(depts.values()),margin=sum(s.total-s.tax-s.cost for s in rows),tax=sum(s.tax for s in rows),count=len(rows))
@app.get("/report.csv")
def report(req:Request,period:str="today",db=Depends(database)):
    check(req,db,[]); out=io.StringIO(); w=csv.writer(out); w.writerow(["Receipt","Date","Department","Mode","Total INR","Tax INR","Cost INR"])
    for s in db.query(Sale).filter(Sale.status=="Paid",Sale.settled>=datetime.combine(period_start(period),time()),Sale.settled<=clock()):
        w.writerow([s.id,s.settled,s.department,s.mode,s.total/100,s.tax/100,s.cost/100])
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=club-sales.csv"})
@app.get("/receipt/{sid}")
def receipt(req:Request,sid:int,db=Depends(database)):
    u=check(req,db,["desk","bar","shop","physio","member"]); s=get(db,Sale,sid)
    allowed=u.role=="owner" or (u.role=="member" and s.member_id==member(db,u).id) or s.department in {"bar":["Bar"],"shop":["Shop"],"desk":["Courts","Memberships"]}.get(u.role,[]) or (u.role=="physio" and db.query(Appointment).filter_by(sale_id=s.id,staff_id=u.id).first())
    require(allowed,"Forbidden",403)
    return template(req,"receipt",user=u,s=s,items=db.query(Item).filter_by(sale_id=s.id).all(),buyer=name_for(db,get(db,Member,s.member_id)) if s.member_id else s.details.get("client","Guest"))
from actions import ROLES
@app.post("/api/{action}")
def mutate(action:str,req:Request,d:dict,db=Depends(database)):
    require(action in ROLES,"Unknown action",404)
    u=check(req,db,ROLES[action]) if ROLES[action] is not None else None
    try:
        result=operate(action,d,req,db,u)
        db.commit()
        return result or {"ok":True}
    except (KeyError,ValueError,TypeError,OverflowError):
        fail("Check the required fields, dates and quantities.")
    except IntegrityError:
        fail("This record conflicts with an existing record.",409)

def operate(a,d,req,db,u):
    def payment():
        v=d.get("mode","UPI"); require(v in ("Cash","Card","UPI"),"Select a payment method."); return v
    def selected(optional=False):
        if u.role=="member":return member(db,u)
        if optional and not d.get("member_id"):return None
        m=get(db,Member,d["member_id"]); require(get(db,User,m.user_id).active,"Member is inactive."); return m
    def shift():
        s=db.query(Shift).filter_by(closed=None).first()
        require(s,"Open a bar shift first.",409); return s
    if a=="register":
        require(d.get("role","member")=="member" and d.get("tier","Free")=="Free","Public registration is Free membership only.",403)
        add_user(db,d,"member"); return {"redirect":"/login?registered=1"}
    if a=="login":
        user=db.query(User).filter_by(email=email(d["email"]),active=True).first()
        require(user and password_ok(d["password"],user.password),"Email or password is incorrect.",403)
        nonce=secrets.token_urlsafe(32); user.sessions=[x for x in user.sessions if x["exp"]>clock().isoformat()][-9:]+[{"h":digest(nonce),"exp":(clock()+timedelta(hours=12)).isoformat()}]
        r=JSONResponse({"redirect":"/dashboard"}); r.set_cookie("club",sign(f"{user.id}:{nonce}"),httponly=True,samesite="strict",secure=req.url.scheme=="https",max_age=43200); return r
    if a=="logout":
        h=digest(unsign(req.cookies["club"]).split(":")[1]); u.sessions=[x for x in u.sessions if x["h"]!=h]
        r=JSONResponse({"redirect":"/"}); r.delete_cookie("club"); return r
    if a=="lead":
        require(d["name"].strip() and d["interest"].strip(),"Enter a name and interest.")
        db.add(Lead(name=d["name"],email=email(d["email"]),interest=d["interest"],trial=d.get("type")=="Trial"))
    if a in ("walkin","add_user"):
        role="member" if a=="walkin" else d["role"]
        require(role in ("member","desk","shop","bar","physio"),"Invalid account role.")
        add_user(db,d,role)
    if a in ("edit_user","archive"):
        target=get(db,User,d["id"]); require(target.role!="owner","Owner account is protected.")
        if a=="archive":target.active=False; target.sessions=[]
        else:
            name=d["name"].strip(); require(name,"Enter a name."); target.name=name; target.email=email(d["email"]); target.active=d["active"]=="Yes"
            if target.role=="member" and d.get("dob"):
                dob=date.fromisoformat(d["dob"]); require(date(1900,1,1)<=dob<=clock().date(),"Invalid DOB"); member(db,target).dob=dob
            if target.role!="member":
                require(d["role"] in ("desk","bar","shop","physio"),"Invalid staff role."); target.role=d["role"]
            target.sessions=[]
    if a=="upgrade":
        m=selected(); tier=d["tier"]; require(tier in ("Gold","Silver","Junior"),"Invalid plan.")
        today=clock().date(); require(tier!="Junior" or adult_on(m.dob)>today,"Junior requires age under 18.")
        end=(max(today-timedelta(days=1),m.expiry) if m.expiry and effective(m)==tier else today-timedelta(days=1))+timedelta(days=30)
        m.tier=tier; m.expiry=min(end,adult_on(m.dob)-timedelta(days=1)) if tier=="Junior" else end
        s=sale(db,u,m,"Memberships",payment()); line(db,s,tier+" membership through "+str(m.expiry),{"Silver":150000,"Gold":300000,"Junior":80000}[tier])
    if a in ("book","trial"):
        m=selected()
        if a=="trial":
            lead=get(db,Lead,d["lead_id"]); require(lead.trial and not lead.booking_id,"Trial already confirmed or unavailable.",409)
        b=book(db,u,m,get(db,Court,d["court_id"]),datetime.fromisoformat(d["start"]),payment())
        if a=="trial":lead.booking_id=b.id
        return {"message":"Court confirmed","receipt":b.sale_id}
    if a=="cancel":
        b=get(db,Booking,d["id"]); require(u.role!="member" or b.member_id==member(db,u).id,"Forbidden",403)
        require(b.status=="Booked" and b.start>clock(),"Only future active bookings can be cancelled.")
        b.status="Cancelled"; old=get(db,Sale,b.sale_id)
        refund=sale(db,u,get(db,Member,b.member_id),"Courts",old.mode); line(db,refund,f"Reversal of receipt {old.id}",-old.total)
    if a=="lead_stage":
        lead=get(db,Lead,d["id"]); stages=["New","Contacted","Quote Sent","Converted"]; idx=stages.index(lead.stage)
        require(idx<3 and d["stage"]==stages[idx+1],"Advance one stage at a time."); lead.stage=d["stage"]
    if a=="order":
        dept=d["department"]; require(dept in ("Shop","Bar") and (u.role!="shop" or dept=="Shop"),"Forbidden",403)
        m=selected(True); method=d["fulfilment"]; require(method in (("Counter","Pickup","Delivery") if dept=="Shop" else ("Table","Pickup",)),"Invalid fulfilment.")
        if method=="Delivery":require(d.get("address","").strip(),"Delivery address required.")
        s=sale(db,u,m,dept,payment(),details={"fulfilment":method,"state":"Completed" if method=="Counter" else "Received","address":d.get("address","")},shift_id=shift().id if dept=="Bar" else None)
        products(db,s,m,dept,d["cart"],1); return {"receipt":s.id,"message":"Order received"}
    if a=="fulfil":
        s=get(db,Sale,d["id"]); require(s.department=="Shop" and s.details.get("state")=="Received","Order already fulfilled or unavailable.",409)
        s.details={**s.details,"state":"Dispatched" if s.details["fulfilment"]=="Delivery" else "Collected"}
    if a=="adjust":
        p=get(db,Product,d["id"]); delta=int(d["delta"]); require(p.department=="Shop" and 0<=p.stock_on_hand+delta<=1000000,"Invalid adjustment."); p.stock_on_hand+=delta
    if a=="open_shift":
        require(not db.query(Shift).filter_by(closed=None).first(),"Register already open.",409); db.add(Shift(staff_id=u.id,opened=clock()))
    if a=="close_shift":
        h=shift(); require(not db.query(Sale).filter_by(shift_id=h.id,status="Open").count(),"Settle open tabs first.",409)
        h.summary={k:sum(s.total for s in db.query(Sale).filter_by(shift_id=h.id,mode=k,status="Paid")) for k in ("Cash","Card","UPI")}; h.closed=clock()
    if a=="tab":
        h=shift(); table=int(d["table"]); require(1<=table<=8,"Invalid table.")
        require(all(s.details.get("table")!=table for s in db.query(Sale).filter_by(department="Bar",status="Open")),"Table already open.",409)
        sale(db,u,selected(True),"Bar","Pending","Open",shift_id=h.id,details={"table":table})
    if a in ("batch","settle"):
        s=get(db,Sale,d["id"]); require(s.department=="Bar" and s.status=="Open","Tab already settled.",409)
        if a=="batch":
            batch=db.query(Item).filter_by(sale_id=s.id).count()+1
            products(db,s,get(db,Member,s.member_id) if s.member_id else None,"Bar",d["cart"],batch)
        else:
            require(s.total>0,"Add items first."); s.mode=payment(); s.status="Paid"; s.settled=clock(); return {"receipt":s.id}
    if a=="ticket":
        i=get(db,Item,d["id"]); stages=["New","Preparing","Ready","Served"]; require(i.ticket in stages[:-1],"Ticket closed.",409)
        require(d["state"]==stages[stages.index(i.ticket)+1],"Ticket changed; refresh.",409); i.ticket=d["state"]
    if a=="appointment":
        m=selected(); p=get(db,User,d["staff_id"]); t=datetime.fromisoformat(d["start"])
        require(p.role=="physio" and p.active and t>clock() and 8<=t.hour<19 and t.minute in (0,30) and not(t.second or t.microsecond),"Choose a future 30-minute slot, 08:00–19:00.")
        q=db.query(Appointment).filter_by(start=t); require(not q.filter((Appointment.staff_id==p.id)|(Appointment.member_id==m.id)).count(),"Appointment occupied.",409)
        s=sale(db,u,m,"Physio",payment()); line(db,s,"Physio · 30 minutes",50000); db.add(Appointment(member_id=m.id,staff_id=p.id,start=t,sale_id=s.id))
    if a=="complete":
        ap=get(db,Appointment,d["id"]); require(u.role=="owner" or ap.staff_id==u.id,"Forbidden",403); require(ap.status=="Booked" and ap.start<=clock(),"Only a started session can be completed."); ap.status="Completed"; ap.summary=d.get("summary","")
    if a=="invoice":
        from decimal import Decimal
        amount=int(Decimal(str(d["amount"]))*100); tax=int(Decimal(str(d["tax"]))*100)
        require(0<amount<10**12 and 0<=tax<=amount and d["client"].strip(),"Invalid client or invoice amount.")
        s=sale(db,u,None,"B2B",payment(),details={"client":d["client"]}); line(db,s,d["description"],amount+tax); s.tax=tax; return {"receipt":s.id}
    if a in ("leave","schedule","payroll"):
        target=get(db,User,d["staff_id"]) if u.role=="owner" else u
        require(target.active and target.role!="member","Select active staff.")
        if a=="payroll":
            from decimal import Decimal
            amount=int(Decimal(str(d["amount"]))*100); datetime.strptime(d["period"],"%Y-%m"); require(amount>0,"Invalid pay.")
            require(not db.query(Payroll).filter_by(staff_id=target.id,period=d["period"]).first(),"Period already recorded.",409)
            db.add(Payroll(staff_id=target.id,period=d["period"],amount=amount))
        elif a=="leave":
            start=date.fromisoformat(d["start"]); end=date.fromisoformat(d["end"]); require(end>=start,"Check leave dates.")
            db.add(Leave(staff_id=target.id,start=start,end=end,reason=d["reason"]))
        else:
            start=datetime.fromisoformat(d["start"]); end=datetime.fromisoformat(d["end"]); require(end>start and all(end<=datetime.fromisoformat(x["start"]) or start>=datetime.fromisoformat(x["end"]) for x in target.shifts),"Shift overlaps or ends too early.")
            target.shifts=target.shifts+[{"start":start.isoformat(),"end":end.isoformat()}]
    if a=="decide":
        leave=get(db,Leave,d["id"]); require(leave.status=="Pending" and d["status"] in ("Approved","Declined"),"Invalid decision."); leave.status=d["status"]



@app.get("/api/physio/slots")
def physio_slots(req:Request,staff_id:int,day:date,db=Depends(database)):
    u=check(req,db,["member"])
    p=get(db,User,staff_id)
    require(p.role=="physio" and p.active,"Practitioner unavailable.")
    profile=member(db,u)
    booked=db.query(Appointment).filter(Appointment.start>=datetime.combine(day,time()),Appointment.start<datetime.combine(day+timedelta(days=1),time()))
    if profile:
        booked=booked.filter((Appointment.staff_id==staff_id)|(Appointment.member_id==profile.id))
    else: booked=booked.filter_by(staff_id=staff_id)
    taken={a.start for a in booked}
    times=[datetime.combine(day,time(n//2,30*(n%2))) for n in range(16,38)]
    return [t.isoformat(timespec="minutes") for t in times if t>clock() and t not in taken]
