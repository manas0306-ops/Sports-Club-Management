from datetime import date,datetime,timedelta
from pathlib import Path
from database import Base,engine,Session
from models import *
from security import password_hash
from services import clock

def seed():
    Base.metadata.create_all(engine)
    with Session.begin() as db:
        if db.query(User).count(): return
        hashed=password_hash("password123")
        for i,role in enumerate(["owner","desk","bar","shop","physio","silver","gold","free"]):
            user=User(email=role+"@club.com",name=["Maanas Pandey","Ananya Rao","Arjun Shah","Riya Sen","Neha Singh","Aarav Mehta","Isha Gill","Kabir Das"][i],role=role if i<5 else "member",password=hashed)
            db.add(user); db.flush()
            if i>=5: db.add(Member(user_id=user.id,dob=date(2004,4,12),tier=role.title(),expiry=clock().date()+timedelta(days=30) if role!="free" else None))
        for sport,kind,price in [("Tennis","Hard",600),("Padel","Glass",800),("Badminton","Indoor",400),("Cricket","Nets",500)]:
            db.add(Court(name=sport+" 01",sport=sport,kind=kind,price=price*100,social=True))
        for name,cat,p,c,n in [("Pro Carbon Racket","Rackets",4500,2900,1),("Match Ball Set","Balls",350,190,20),("Court Shoes · UK 8","Shoes",3200,2000,5),("Club Polo · M","Apparel",1200,650,8),("Grip Tape","Accessories",180,70,12),("Iced Latte","Café",180,70,40),("Grilled Sandwich","Café",220,85,30),("Lime Soda","Café",90,30,50)]:
            db.add(Product(name=name,department="Bar" if cat=="Café" else "Shop",category=cat,price=p*100,cost=c*100,stock_on_hand=n))
        p_csv = Path(__file__).resolve().parent / "data" / "products.csv"
        if p_csv.exists():
            import csv
            with open(p_csv, 'r', encoding='utf-8') as pf:
                for r in csv.DictReader(pf):
                    db.add(Product(
                        name=r['name'].strip(),
                        department="Shop",
                        category=r['category'].strip(),
                        price=int(float(r['price']) * 100),
                        cost=int(float(r['wholesale_price']) * 100),
                        stock_on_hand=int(r['quantity']),
                        reorder_level=10
                    ))
        db.add(Shift(staff_id=3,opened=clock()))
        for i in range(12):
            dept=["Courts","Shop","Bar","Physio","Memberships"][i%5]
            amount=[300,350,180,500,1500][i%5]*100
            moment=clock()-timedelta(days=i//3)
            s=Sale(member_id=1,actor_id=1,department=dept,total=amount,mode=["Cash","Card","UPI"][i%3],created=moment,settled=moment,status="Paid")
            db.add(s); db.flush(); db.add(Item(sale_id=s.id,name={"Courts":"Tennis session","Shop":"Match Ball Set","Bar":"Iced Latte","Physio":"Recovery session","Memberships":"Silver membership"}[dept],price=amount,total=amount))
        db.add_all([
            Lead(name="Tara Sethi",email="tara@example.com",interest="Friday padel trial",trial=True,created=clock()-timedelta(hours=14)),
            Lead(name="Dev Roy",email="dev@example.com",interest="Corporate membership",stage="Contacted",created=clock()-timedelta(hours=12)),
            Lead(name="Aanya Sharma",email="aanya@example.com",interest="Tennis Junior Squad & Coaching",trial=True,created=clock()-timedelta(hours=1,minutes=15)),
            Lead(name="Vikram Malhotra",email="vikram.m@corporatesports.in",interest="Corporate Executive Membership",stage="New",trial=False,created=clock()-timedelta(hours=3,minutes=20)),
            Leave(staff_id=3,start=clock().date()+timedelta(days=2),end=clock().date()+timedelta(days=3),reason="Family visit"),
            Payroll(staff_id=2,period=clock().date().strftime("%Y-%m"),amount=2800000)
        ])
        crm_csv = Path(__file__).resolve().parent / "data" / "crm_connected_users.csv"
        if crm_csv.exists():
            import csv
            with open(crm_csv, 'r', encoding='utf-8') as cf:
                crm_leads = []
                for r in csv.DictReader(cf):
                    conns = int(r['total_connections'])
                    stg = "Converted" if conns>=30 else ("Quote Sent" if conns>=15 else ("Contacted" if (r['status']=="Online" or conns>=5) else "New"))
                    crm_leads.append(Lead(
                        user_code=r['user_id'].strip(),
                        name=r['name'].strip(),
                        email=r['email'].strip(),
                        phone=r['phone'].strip(),
                        city=r['city'].strip(),
                        state=r['state'].strip(),
                        proxy_name=r['proxy_name'].strip(),
                        proxy_ip=r['proxy_ip'].strip(),
                        protocol=r['protocol'].strip(),
                        status=r['status'].strip(),
                        total_connections=conns,
                        data_used_mb=r['data_used_mb'].strip(),
                        interest=f"Proxy Route: {r['proxy_name'].strip()} ({r['protocol'].strip()}) · {r['city'].strip()}, {r['state'].strip()} · {r['data_used_mb'].strip()} MB",
                        stage=stg,
                        trial=False,
                        created=datetime.strptime(r['last_connected'].strip(), "%Y-%m-%d %H:%M:%S")
                    ))
                db.add_all(crm_leads)
if __name__=="__main__":
    seed()
    print("Club database ready.")
