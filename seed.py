from datetime import date,datetime,timedelta
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
        db.add(Shift(staff_id=3,opened=clock()))
        for i in range(12):
            dept=["Courts","Shop","Bar","Physio","Memberships"][i%5]
            amount=[300,350,180,500,1500][i%5]*100
            moment=clock()-timedelta(days=i//3)
            s=Sale(member_id=1,actor_id=1,department=dept,total=amount,mode=["Cash","Card","UPI"][i%3],created=moment,settled=moment,status="Paid")
            db.add(s); db.flush(); db.add(Item(sale_id=s.id,name={"Courts":"Tennis session","Shop":"Match Ball Set","Bar":"Iced Latte","Physio":"Recovery session","Memberships":"Silver membership"}[dept],price=amount,total=amount))
        db.add_all([Lead(name="Tara Sethi",email="tara@example.com",interest="Friday padel trial",trial=True),Lead(name="Dev Roy",email="dev@example.com",interest="Corporate membership",stage="Contacted"),Leave(staff_id=3,start=clock().date()+timedelta(days=2),end=clock().date()+timedelta(days=3),reason="Family visit"),Payroll(staff_id=2,period=clock().date().strftime("%Y-%m"),amount=2800000)])
if __name__=="__main__":
    seed()
    print("Club database ready.")
