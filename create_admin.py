"""
CLI Utility: Secure Initial Administrator Creation
Usage:
    python create_admin.py --username admin --email admin@champions.club --password ChampionsAdmin2026!
"""
import sys
import argparse
from app.database import SessionLocal, Base, engine
import app.models # registers models
from app.models.user import User, UserRole
from app.services.auth_security import hash_password

def create_admin(username: str, email: str, password: str):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check existing
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            if existing.primary_role != UserRole.ADMIN.value:
                print(f"Error: User '{existing.username}' exists with role '{existing.primary_role}'. Cannot overwrite.")
                return False
            # Update password
            existing.password_hash = hash_password(password)
            existing.is_active = True
            db.commit()
            print(f"Success: Administrator '{username}' password updated successfully.")
            return True

        admin_user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            primary_role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Success: Administrator '{username}' created successfully (ID: {admin_user.id}, Role: {admin_user.primary_role})!")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure Admin Creation for The Champions Club")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@champions.club", help="Admin email")
    parser.add_argument("--password", default="ChampionsAdmin2026!", help="Admin password")
    args = parser.parse_args()

    create_admin(args.username, args.email, args.password)
