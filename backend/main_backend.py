# backend/main.py
from fastapi import FastAPI
from routes import auth, doctor, technician, equipment, users, admin,patients
from database import create_tables
from dotenv import load_dotenv

load_dotenv()


create_tables() 

app = FastAPI(title="Medical Lab System")

app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(technician.router, prefix="/technicians")
app.include_router(equipment.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(patients.router)
