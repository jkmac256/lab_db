# backend/main.py
from fastapi import FastAPI
from routes import auth, doctor, technician, equipment, users, admin,patients, superadmin
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
app.include_router(superadmin.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_backend:app", host="0.0.0.0", port=8000)
