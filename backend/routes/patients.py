# backend/routes/patients.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from dependencies import require_role  # if you want to restrict access

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/all/", dependencies=[Depends(require_role("ADMIN"))])
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found")
    return patients
