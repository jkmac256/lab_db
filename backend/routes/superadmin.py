# backend/routes/superadmin.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Laboratory
from schemas import LaboratoryCreate, LaboratoryOut
from database import get_db

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])

@router.post("/labs", response_model=LaboratoryOut)
def create_lab(lab: LaboratoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Laboratory).filter(Laboratory.name == lab.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lab with this name already exists.")

    new_lab = Laboratory(
        name=lab.name,
        address=lab.address,
        contact_email=lab.contact_email
    )
    db.add(new_lab)
    db.commit()
    db.refresh(new_lab)
    return new_lab


@router.get("/labs", response_model=list[LaboratoryOut])
def list_labs(db: Session = Depends(get_db)):
    labs = db.query(Laboratory).all()
    return labs


@router.delete("/labs/{lab_id}")
def delete_lab(lab_id: int, db: Session = Depends(get_db)):
    lab = db.query(Laboratory).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found.")

    db.delete(lab)
    db.commit()
    return {"detail": "Lab deleted."}
