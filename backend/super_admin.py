# create_super_admin.py

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, User

# ✅ Make sure all tables exist:
Base.metadata.create_all(bind=engine)

# ✅ Setup password hashing:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_super_admin():
    db: Session = SessionLocal()

    # ✅ Your super admin credentials:
    full_name = "Super Admin"
    email = "mjkwagala@gmail.com"
    plain_password = "@mac#j1."  

    # ✅ Hash the password:
    hashed_password = pwd_context.hash(plain_password)

    # ✅ Check if already exists:
    existing = db.query(User).filter(User.role == "SUPER_ADMIN").first()
    if existing:
        print("A SUPER_ADMIN already exists. Aborting.")
        db.close()
        return

    new_admin = User(
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        role="SUPER_ADMIN",
        laboratory_id=None  # SUPER_ADMIN does not belong to any lab
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    print(f"✅ SUPER_ADMIN created: {new_admin.full_name} - {new_admin.email}")
    db.close()

if __name__ == "__main__":
    create_super_admin()
