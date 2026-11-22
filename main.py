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
tpl.env.globals.update(effective=effective,membership_status=membership_status,now=clock,rate=rate)
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
    u=current(req,db)
    m=member(db,u) if u else None
    return template(req,"index",user=u,m=m,courts=db.query(Court).all(),gear=db.query(Product).filter_by(department="Shop").all())
@app.get("/login")
def login(req:Request): return template(req,"login",user=None)
@app.get("/api/availability")
def availability(day:date,sport:str="",kind:str="",db=Depends(database)):
    courts=db.query(Court).all(); output=[]
    require(abs((day-clock().date()).days)<=92,"Date outside calendar")
    for c in courts:
        if sport and sport!=c.sport or kind and kind!=c.kind: continue
        rows=db.query(Booking).filter_by(court_id=c.id).filter(Booking.status.in_(["Booked","Pending","Maintenance"])).filter(Booking.start>=datetime.combine(day,time()),Booking.start<datetime.combine(day+timedelta(days=1),time())).all()
        times=[]
        for half in range(12,43):
            t=datetime.combine(day,time(half//2,30*(half%2))); k=slot(c,t)
            maint=any(b.status=="Maintenance" and b.start<t+timedelta(hours=1) and b.end>t for b in rows)
            occupied=sum(b.start<t+timedelta(hours=1) and b.end>t for b in rows if b.status in ("Booked","Pending"))
            if maint:
                times.append(dict(start=t.isoformat(timespec="minutes"),kind="Maintenance",left=0))
            else:
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
    if role in ("desk","owner"):
        data["members"]=[dict(id=x.id,user_id=x.user_id,name=name_for(db,x),tier=effective(x),expiry=x.expiry) for x in db.query(Member).join(User).filter(User.active==True)]
    if role in ("member","physio","owner"):
        data["physios"]=db.query(User).filter_by(role="physio",active=True).all()
        q=db.query(Appointment)
        if m:q=q.filter_by(member_id=m.id)
        if role=="physio":q=q.filter_by(staff_id=u.id).filter(Appointment.start>=datetime.combine(day,time()),Appointment.start<datetime.combine(day+timedelta(days=1),time()))
        data["appointments"]=q.order_by(Appointment.start).all()
    if role in ("desk","owner"):
        raw_leads=db.query(Lead).order_by(Lead.created.desc()).all()
        users_by_email={usr.email.lower(): usr.id for usr in db.query(User).all()}
        members_by_id={mem.id: mem.user_id for mem in db.query(Member).all()}
        bookings_map={bk.id: bk.member_id for bk in db.query(Booking).all()}
        now_dt = clock()
        for l in raw_leads:
            uid = users_by_email.get(l.email.lower()) if l.email else None
            if not uid and l.booking_id:
                mid = bookings_map.get(l.booking_id)
                if mid: uid = members_by_id.get(mid)
            l.user_id = uid
            diff = now_dt - l.created if l.created else timedelta(0)
            secs = max(0, int(diff.total_seconds()))
            if secs < 60: l.time_since = "Just now"
            elif secs < 3600: l.time_since = f"{secs // 60}m ago"
            elif secs < 86400: l.time_since = f"{secs // 3600}h {(secs % 3600) // 60}m ago"
            else: l.time_since = f"{secs // 86400}d ago"
        data["leads"]=raw_leads
    if role in ("bar","shop","member","owner","desk"):
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
    if role in ("owner","desk"):
        data["all_sales"]=db.query(Sale).order_by(Sale.id.desc()).all()
        data["all_bookings"]=db.query(Booking).order_by(Booking.start.desc()).all()
    target_sales=data.get("all_sales",data["sales"])
    s_ids=[s.id for s in target_sales]
    items_map={}
    if s_ids:
        for it in db.query(Item).filter(Item.sale_id.in_(s_ids)).all():
            items_map.setdefault(it.sale_id,[]).append(it)
    data["items_by_sale"]=items_map
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
@app.get("/upgrade/bill")
def upgrade_bill(req:Request,tier:str="Gold",mode:str="UPI",member_id:int|None=None,db=Depends(database)):
    u=current(req,db)
    if not u: return RedirectResponse("/login",303)
    require(tier in ("Gold","Silver","Junior"),"Invalid plan tier.",400)
    require(mode in ("UPI","Card","Cash"),"Invalid payment tender.",400)
    if u.role=="member":
        m=member(db,u)
    elif u.role in ("owner","desk"):
        m=db.get(Member,member_id) if member_id else db.query(Member).first()
    else:
        m=None
    require(m,"Member account not found.",404)
    target_user=get(db,User,m.user_id)
    today=clock().date()
    if tier=="Junior":
        require(adult_on(m.dob)>today,"Junior membership requires age under 18.",400)
    prices={"Silver":150000,"Gold":300000,"Junior":80000}
    price=prices[tier]
    end=(max(today-timedelta(days=1),m.expiry) if m.expiry and effective(m)==tier else today-timedelta(days=1))+timedelta(days=30)
    if tier=="Junior":
        end=min(end,adult_on(m.dob)-timedelta(days=1))
    bill_ref=f"CC-BILL-{today.strftime('%Y%m%d')}-{m.id}"
    return template(req,"bill",user=u,m=m,target_user=target_user,tier=tier,mode=mode,price=price,today=today,end=end,bill_ref=bill_ref)
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
        mid=d.get("member_id")
        if optional and (mid is None or str(mid).strip() in ("", "0")):return None
        clean_mid=None
        if mid is not None and str(mid).strip()!="":
            import re
            nums=re.findall(r'\d+',str(mid))
            if nums:clean_mid=int(nums[0])
        if clean_mid is None:
            if optional:return None
            fail("Member account not found or inactive.")
        m=db.get(Member,clean_mid)
        if not m:
            m=db.query(Member).filter_by(user_id=clean_mid).first()
        require(m and get(db,User,m.user_id).active,"Member account not found or inactive.")
        return m
    def shift():
        s=db.query(Shift).filter_by(closed=None).first()
        require(s,"Open a bar shift first.",409); return s
    if a=="register":
        require(d.get("role","member")=="member" and d.get("tier","Free")=="Free","Public registration is Free membership only.",403)
        user=add_user(db,d,"member")
        nonce=secrets.token_urlsafe(32)
        user.sessions=[{"h":digest(nonce),"exp":(clock()+timedelta(hours=12)).isoformat()}]
        r=JSONResponse({"redirect":"/dashboard"})
        r.set_cookie("club",sign(f"{user.id}:{nonce}"),httponly=True,samesite="strict",secure=req.url.scheme=="https",max_age=43200)
        return r
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
        price={"Silver":150000,"Gold":300000,"Junior":80000}[tier]
        m.tier=tier; m.expiry=min(end,adult_on(m.dob)-timedelta(days=1)) if tier=="Junior" else end
        if u.role=="member":
            ref=d.get("payment_ref","").strip() or "PENDING-UTR"
            s=sale(db,u,m,"Memberships",payment(),status="Pending")
            line(db,s,tier+" membership plan request (Pending Approval)",price)
            details=dict(s.details or {})
            details["payment_verified"]=False
            details["payment_ref"]=ref
            details["requested_tier"]=tier
            s.details=details
            return {"receipt":s.id,"message":f"Upgrade request to {tier} submitted! Front desk / admin will verify your payment UTR and activate your tier."}
        else:
            m.tier=tier; m.expiry=min(end,adult_on(m.dob)-timedelta(days=1)) if tier=="Junior" else end
            s=sale(db,u,m,"Memberships",payment(),status="Paid")
            line(db,s,tier+" membership through "+str(m.expiry),price)
            details=dict(s.details or {})
            if d.get("payment_ref"): details["payment_ref"]=d["payment_ref"].strip()
            details["payment_verified"]=True
            details["verified_by"]=u.name
            details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
            s.details=details
            return {"receipt":s.id,"message":f"Successfully upgraded to {tier} membership!"}
    if a in ("book","trial"):
        m=selected()
        if a=="trial":
            lead=get(db,Lead,d["lead_id"]); require(lead.trial and not lead.booking_id,"Trial already confirmed or unavailable.",409)
        c=get(db,Court,d["court_id"])
        start=datetime.fromisoformat(d["start"])
        kind=slot(c,start)
        pct=100 if kind=="Social" else rate(m,"Courts",start.date())
        is_free = (pct == 100) or (a=="trial")

        if u.role=="member":
            if is_free:
                b=book(db,u,m,c,start,"Included",status="Booked")
                s=get(db,Sale,b.sale_id)
                details=dict(s.details or {})
                details["payment_verified"]=True
                details["verified_by"]="System (Gold Tier Privileges)"
                details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
                s.details=details
                return {"message":"Court confirmed (Included in your Gold membership).","receipt":b.sale_id}
            else:
                ref=d.get("payment_ref","").strip() or "PENDING-UTR"
                b=book(db,u,m,c,start,payment(),status="Pending")
                s=get(db,Sale,b.sale_id)
                details=dict(s.details or {})
                details["payment_verified"]=False
                details["payment_ref"]=ref
                s.details=details
                return {"message":"Court reservation submitted! Status: ⏳ Pending Admin Verification. Front desk will verify your payment UTR and confirm your reservation.","receipt":b.sale_id}
        else:
            b=book(db,u,m,c,start,payment(),status="Booked")
            if a=="trial":lead.booking_id=b.id
            s=get(db,Sale,b.sale_id)
            details=dict(s.details or {})
            if d.get("payment_ref"): details["payment_ref"]=d["payment_ref"].strip()
            details["payment_verified"]=True
            details["verified_by"]=u.name
            details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
            s.details=details
            return {"message":"Court confirmed by Front Desk","receipt":b.sale_id}
    if a=="cancel":
        b=get(db,Booking,d["id"]); require(u.role!="member" or b.member_id==member(db,u).id,"Forbidden",403)
        require(b.status in ("Booked","Pending") and b.start>clock(),"Only future active bookings can be cancelled.")
        b.status="Cancelled"; old=get(db,Sale,b.sale_id)
        refund=sale(db,u,get(db,Member,b.member_id),"Courts",old.mode); line(db,refund,f"Reversal of receipt {old.id}",-old.total)
        return {"message":"Court booking cancelled. Full reversal receipt issued."}
    if a=="lead_stage":
        lead=get(db,Lead,d["id"]); stages=["New","Contacted","Quote Sent","Converted"]; idx=stages.index(lead.stage)
        require(idx<3 and d["stage"]==stages[idx+1],"Advance one stage at a time."); lead.stage=d["stage"]
    if a=="order":
        dept=d["department"]; require(dept in ("Shop","Bar") and (u.role!="shop" or dept=="Shop"),"Forbidden",403)
        m=selected(True); method=d["fulfilment"]; require(method in (("Counter","Pickup","Delivery") if dept=="Shop" else ("Table","Pickup",)),"Invalid fulfilment.")
        if method=="Delivery":require(d.get("address","").strip(),"Delivery address required.")
        if u.role=="member":
            ref=d.get("payment_ref","").strip() or "PENDING-UTR"
            details={"fulfilment":method,"state":"Payment Review","address":d.get("address","")}
            details["payment_verified"]=False
            details["payment_ref"]=ref
            if d.get("delivery_notes"): details["delivery_notes"]=d["delivery_notes"].strip()
            s=sale(db,u,m,dept,payment(),status="Pending",details=details,shift_id=shift().id if dept=="Bar" else None)
            products(db,s,m,dept,d["cart"],1)
            return {"receipt":s.id,"message":"Order submitted! Status: ⏳ Payment Under Review. Front desk / staff will verify your payment UTR and confirm your order."}
        else:
            details={"fulfilment":method,"state":"Completed" if method=="Counter" else "Received","address":d.get("address","")}
            if d.get("payment_ref"): details["payment_ref"]=d["payment_ref"].strip()
            if d.get("delivery_notes"): details["delivery_notes"]=d["delivery_notes"].strip()
            details["payment_verified"]=True
            details["verified_by"]=u.name
            details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
            s=sale(db,u,m,dept,payment(),status="Paid",details=details,shift_id=shift().id if dept=="Bar" else None)
            products(db,s,m,dept,d["cart"],1)
            return {"receipt":s.id,"message":"POS order recorded."}
    if a=="fulfil":
        s=get(db,Sale,d["id"]); require(s.department=="Shop" and s.details.get("state") in ("Received","Payment Review"),"Order already fulfilled or unavailable.",409)
        s.details={**s.details,"state":"Dispatched" if s.details["fulfilment"]=="Delivery" else "Collected","status_updated_at":clock().strftime("%d %b, %H:%M"),"payment_verified":True}
    if a=="update_order_status":
        s=get(db,Sale,d["id"])
        state=d.get("state","Completed")
        require(state in ("Received","Dispatched","Collected","Completed","Out for Delivery","Delivered"),"Invalid status.")
        s.details={**s.details,"state":state,"status_updated_at":clock().strftime("%d %b, %H:%M")}
        return {"message":f"Order CC-{s.id:05d} updated to {state}."}
    if a=="verify_payment":
        s=get(db,Sale,d["id"])
        details=dict(s.details or {})
        details["payment_verified"]=True
        details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
        details["verified_by"]=u.name
        if d.get("notes"): details["verification_notes"]=d["notes"].strip()
        if details.get("state")=="Payment Review":
            details["state"]="Received"
        s.details=details
        s.status="Paid"
        s.settled=clock()
        linked_booking=db.query(Booking).filter_by(sale_id=s.id).first()
        if linked_booking:
            linked_booking.status="Booked"
        if s.department=="Memberships" and details.get("requested_tier"):
            m=db.get(Member,s.member_id)
            if m:
                tier=details["requested_tier"]
                today=clock().date()
                end=(max(today-timedelta(days=1),m.expiry) if m.expiry and effective(m)==tier else today-timedelta(days=1))+timedelta(days=30)
                m.tier=tier
                m.expiry=min(end,adult_on(m.dob)-timedelta(days=1)) if tier=="Junior" else end
        return {"message":f"Payment for Receipt CC-{s.id:05d} verified and confirmed."}
    if a=="approve_booking":
        b=get(db,Booking,d["id"])
        b.status="Booked"
        if b.sale_id:
            s=get(db,Sale,b.sale_id)
            details=dict(s.details or {})
            details["payment_verified"]=True
            details["verified_at"]=clock().strftime("%d %b %Y, %H:%M IST")
            details["verified_by"]=u.name
            s.details=details
            if s.status=="Pending":
                s.status="Paid"
                s.settled=clock()
        return {"message":f"Court reservation #{b.id} payment verified and confirmed."}
    if a in ("reject_payment","reject_booking"):
        reason=d.get("reason","Payment verification declined by administrator.").strip() or "Declined by administrator."
        if a=="reject_payment":
            s=get(db,Sale,d["id"])
            b=db.query(Booking).filter_by(sale_id=s.id).first()
        else:
            b=get(db,Booking,d["id"])
            s=get(db,Sale,b.sale_id) if b.sale_id else None
        if b and b.status in ("Booked","Pending"):
            b.status="Cancelled"
        if s:
            s_details=dict(s.details or {})
            s_details["payment_verified"]=False
            s_details["approval_status"]="Rejected"
            s_details["rejection_reason"]=reason
            s_details["rejected_at"]=clock().strftime("%d %b %Y, %H:%M IST")
            s_details["rejected_by"]=u.name
            s.details=s_details
            if s.status=="Paid":
                s.status="Cancelled"
                refund=sale(db,u,get(db,Member,s.member_id) if s.member_id else None,s.department,s.mode)
                line(db,refund,f"Rejection reversal of CC-{s.id:05d}",-s.total)
            elif s.status=="Pending":
                s.status="Cancelled"
        return {"message":"Payment approval rejected and court booking released."}
    if a=="confirm_all_bookings":
        require(u.role in ("owner","desk"),"Forbidden",403)
        confirmed_count=0
        now_str=clock().strftime("%d %b %Y, %H:%M IST")
        for s in db.query(Sale).all():
            if not (s.details and s.details.get("payment_verified")) and s.status!="Cancelled":
                s_details=dict(s.details or {})
                s_details["payment_verified"]=True
                s_details["verified_at"]=now_str
                s_details["verified_by"]=u.name
                s_details["verification_notes"]=f"Bulk verified by {u.name}"
                s.details=s_details
                if s.status=="Pending":
                    s.status="Paid"
                    s.settled=clock()
                confirmed_count+=1
        for b in db.query(Booking).filter(Booking.status.in_(["Pending","Received"])).all():
            b.status="Booked"
            confirmed_count+=1
            if b.sale_id:
                bs=db.get(Sale,b.sale_id)
                if bs:
                    bs_details=dict(bs.details or {})
                    bs_details["payment_verified"]=True
                    bs_details["verified_at"]=now_str
                    bs_details["verified_by"]=u.name
                    bs.details=bs_details
                    if bs.status=="Pending":
                        bs.status="Paid"
                        bs.settled=clock()
        return {"message":f"Successfully verified and confirmed {confirmed_count} pending bookings and payments."}
    if a=="reject_all_bookings":
        require(u.role in ("owner","desk"),"Forbidden",403)
        reason=d.get("reason","Bulk rejected by administrator.").strip() or "Bulk rejected by administrator."
        now_str=clock().strftime("%d %b %Y, %H:%M IST")
        rejected_count=0
        for b in db.query(Booking).filter(Booking.status.in_(["Booked","Pending","Received"]),Booking.start>clock()).all():
            bs=db.get(Sale,b.sale_id) if b.sale_id else None
            is_unverified=bs and not (bs.details and bs.details.get("payment_verified"))
            if b.status in ("Pending","Received") or is_unverified:
                b.status="Cancelled"
                rejected_count+=1
                if bs and bs.status!="Cancelled":
                    bs_details=dict(bs.details or {})
                    bs_details["payment_verified"]=False
                    bs_details["approval_status"]="Rejected"
                    bs_details["rejection_reason"]=reason
                    bs_details["rejected_at"]=now_str
                    bs_details["rejected_by"]=u.name
                    bs.details=bs_details
                    if bs.status=="Paid":
                        bs.status="Cancelled"
                        refund=sale(db,u,get(db,Member,bs.member_id) if bs.member_id else None,bs.department,bs.mode)
                        line(db,refund,f"Rejection reversal of CC-{bs.id:05d}",-bs.total)
                    elif bs.status=="Pending":
                        bs.status="Cancelled"
        for s in db.query(Sale).all():
            if not (s.details and s.details.get("payment_verified")) and s.status!="Cancelled":
                s_details=dict(s.details or {})
                s_details["payment_verified"]=False
                s_details["approval_status"]="Rejected"
                s_details["rejection_reason"]=reason
                s_details["rejected_at"]=now_str
                s_details["rejected_by"]=u.name
                s.details=s_details
                if s.status=="Paid":
                    s.status="Cancelled"
                    refund=sale(db,u,get(db,Member,s.member_id) if s.member_id else None,s.department,s.mode)
                    line(db,refund,f"Rejection reversal of CC-{s.id:05d}",-s.total)
                elif s.status=="Pending":
                    s.status="Cancelled"
                rejected_count+=1
        return {"message":f"Successfully rejected {rejected_count} pending bookings and payments. Court slots released."}
    if a in ("delete_product", "remove_product"):
        require(u.role in ("owner", "desk", "shop", "bar"), "Forbidden", 403)
        p = get(db, Product, d["id"])
        db.query(Item).filter_by(product_id=p.id).update({"product_id": None})
        p_name = p.name
        db.delete(p)
        db.flush()
        return {"message": f"Product '{p_name}' removed from catalog successfully."}
    if a=="add_product":
        dept=d.get("department","Shop"); require(dept in ("Shop","Bar"),"Invalid department.")
        name=d["name"].strip(); category=d.get("category","Accessories").strip()
        from decimal import Decimal
        price=int(Decimal(str(d["price"]))*100)
        cost=int(Decimal(str(d.get("cost",0)))*100) if d.get("cost") else int(price*0.6)
        stock=int(d.get("stock_on_hand",10))
        require(name and price>0 and stock>=0,"Item name, positive price and valid stock required.")
        p=Product(name=name,department=dept,category=category,price=price,cost=cost,stock_on_hand=stock)
        db.add(p); db.flush()
        return {"message":f"Product '{name}' added to {dept} catalog successfully."}
    if a=="edit_product":
        p=get(db,Product,d["id"])
        if d.get("name"): p.name=d["name"].strip()
        if d.get("category"): p.category=d["category"].strip()
        from decimal import Decimal
        if d.get("price"): p.price=int(Decimal(str(d["price"]))*100)
        if d.get("cost"): p.cost=int(Decimal(str(d["cost"]))*100)
        if "stock_on_hand" in d: p.stock_on_hand=int(d["stock_on_hand"])
        return {"message":f"Product '{p.name}' updated successfully."}
    if a=="block_court":
        require(u.role in ("owner","desk"),"Forbidden",403)
        c=get(db,Court,d["court_id"])
        start=datetime.fromisoformat(d["start"])
        duration=int(d.get("duration",1))
        end=start+timedelta(hours=duration)
        m_admin=db.query(Member).first()
        b=Booking(court_id=c.id,member_id=m_admin.id if m_admin else 1,start=start,end=end,status="Maintenance")
        db.add(b)
        return {"message":f"{c.name} slot at {start.strftime('%H:%M')} blocked for maintenance / hold."}
    if a=="unblock_court":
        require(u.role in ("owner","desk"),"Forbidden",403)
        b=get(db,Booking,d["id"])
        require(b.status=="Maintenance","Only maintenance blocks can be removed.")
        db.delete(b)
        return {"message":"Court maintenance block removed successfully."}
    if a=="update_profile":
        name=d.get("name","").strip()
        require(name,"Name cannot be empty.")
        u.name=name
        return {"message":"Your profile details have been updated."}
    if a=="change_password":
        cur_pw=d.get("current_password","")
        new_pw=d.get("new_password","")
        require(password_ok(cur_pw,u.password),"Current password is incorrect.",403)
        require(8<=len(new_pw.encode())<=72,"New password must be between 8 and 72 characters.")
        u.password=password_hash(new_pw)
        return {"message":"Password updated successfully."}
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
