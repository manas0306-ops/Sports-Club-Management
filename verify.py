"""Run the HTTP workflow checks against a new temporary SQLite database."""
import asyncio
import os
import tempfile
from datetime import timedelta
from pathlib import Path
import httpx

async def verify():
    with tempfile.TemporaryDirectory() as folder:
        os.environ["DATABASE_URL"]="sqlite:///"+(Path(folder)/"test.db").as_posix()
        from main import app,engine,clock
        transport=httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport,base_url="http://club.test",headers={"x-club-request":"1"}) as client:
            async def action(name,data=None,status=200):
                r=await client.post("/api/"+name,json=data or {})
                assert r.status_code==status,(name,r.status_code,r.text)
                return r.json()
            async def login(role):
                await action("login",dict(email=role+"@club.com",password="password123"))
                r=await client.get("/dashboard")
                assert r.status_code==200 and "The Champions Club" in r.text
            assert (await client.get("/")).status_code==200
            assert (await client.get("/report.csv")).status_code==403
            await action("register",dict(role="owner"),403)
            await action("register",dict(name="Junior Member",email="junior@example.com",password="password123",dob=str(clock().date().replace(year=clock().year-12,day=1))))
            await action("login",dict(email="junior@example.com",password="password123"));await action("upgrade",dict(tier="Junior"))
            for role in ("owner","desk","bar","shop","physio","gold","free","silver"):await login(role)
            await action("upgrade",dict(tier="Junior"),422)
            slot=(clock()+timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0)
            async def book(hour,court=1,status=200):
                return await action("book",dict(start=(slot+timedelta(hours=hour)).isoformat(),court_id=court),status)
            result=await book(0)
            assert "300.00" in (await client.get("/receipt/"+str(result["receipt"]))).text
            await book(.5,status=409);await book(2);await book(4,2,409)
            await action("cancel",dict(id=1));await book(.5)
            item=dict(department="Shop",fulfilment="Pickup",cart=[dict(id=1,qty=1)])
            results=await asyncio.gather(*(client.post("/api/order",json=item) for _ in range(2)))
            assert sorted(r.status_code for r in results)==[200,409]
            order=next(r.json()["receipt"] for r in results if r.status_code==200)
            await login("free");assert (await client.get("/receipt/"+str(order))).status_code==403
            await action("order",dict(department="Bar",fulfilment="Pickup",cart=[dict(id=6,qty=1)]))
            await action("appointment",dict(staff_id=5,start=slot.isoformat()))
            await action("appointment",dict(staff_id=5,start=slot.isoformat()),409)
            friday=slot+timedelta(days=(4-slot.weekday())%7)
            social=friday.replace(hour=18)
            for index in range(9):
                addr=f"social{index}@example.com"
                await action("register",dict(name=f"Social {index}",email=addr,password="password123",dob="2005-01-01"))
                await action("login",dict(email=addr,password="password123"))
                await action("book",dict(court_id=2,start=social.isoformat()),409 if index==8 else 200)
            await action("book",dict(court_id=2,start=(social-timedelta(minutes=30)).isoformat()),422)
            await login("shop");await action("fulfil",dict(id=order));await action("adjust",dict(id=1,delta=4));await action("tab",dict(table=1),403)
            await login("bar");await action("tab",dict(table=2,member_id=1))
            from database import Session
            from models import Sale,Item
            with Session() as db:tab=db.query(Sale).filter_by(status="Open").one().id
            await action("batch",dict(id=tab,cart=[dict(id=6,qty=2)]))
            with Session() as db:ticket=db.query(Item).filter_by(sale_id=tab).one().id
            for state in ("Preparing","Ready","Served"):await action("ticket",dict(id=ticket,state=state))
            await action("close_shift",{},409);await action("settle",dict(id=tab,mode="Cash"));await action("close_shift");await action("open_shift")
            await login("desk");await action("lead_stage",dict(id=1,stage="Contacted"))
            await login("owner");await action("decide",dict(id=1,status="Approved"));await action("invoice",dict(client="Club partner",description="Court hire",amount=500,tax=0))
            assert (await client.get("/report.csv")).status_code==200
            await action("logout");assert (await client.get("/receipt/1")).status_code==403
        engine.dispose()
    print("PASS: HTTP dashboards, signup, RBAC, discounts, overlap, cap, cancellation, concurrent checkout, fulfilment, physio, KOT, settlement, CRM, HR, invoices and CSV.")

if __name__=="__main__": asyncio.run(verify())
