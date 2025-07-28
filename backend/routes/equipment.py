from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from models import Equipment, User
from schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/equipment", tags=["Equipment"])

# --- Create equipment via JSON ---
@router.post("/", response_model=EquipmentOut)
def add_equipment_json(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "LAB_TECHNICIAN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only technicians can add equipment."
        )

    eq = Equipment(
        name=payload.name,
        type=payload.type,
        description=payload.description,
        is_available=True,
        last_serviced=datetime.utcnow(),
        added_by_id=current_user.id,
        laboratory_id=current_user.laboratory_id  # ✅ enforce lab link
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


# --- Create equipment via Form ---
@router.post("/form", response_model=EquipmentOut)
def add_equipment_form(
    name: str = Form(...),
    type: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "LAB_TECHNICIAN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only technicians can add equipment."
        )

    eq = Equipment(
        name=name,
        type=type,
        description=description,
        is_available=True,
        last_serviced=datetime.utcnow(),
        added_by_id=current_user.id,
        laboratory_id=current_user.laboratory_id  # ✅ enforce lab link
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


# --- List all equipment in user lab ---
@router.get("/", response_model=List[EquipmentOut])
def list_equipment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Equipment)
        .options(joinedload(Equipment.added_by))
        .filter(Equipment.laboratory_id == current_user.laboratory_id)  # ✅ only this lab
        .all()
    )


# --- Get equipment by ID (in lab) ---
@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment_by_id(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    eq = (
        db.query(Equipment)
        .filter(Equipment.id == equipment_id)
        .filter(Equipment.laboratory_id == current_user.laboratory_id)  # ✅ only this lab
        .first()
    )
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return eq


# --- Update equipment (in lab) ---
@router.put("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int,
    updates: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("ADMIN", "LAB_TECHNICIAN"):
        raise HTTPException(status_code=403, detail="Not authorized to update equipment.")

    eq = (
        db.query(Equipment)
        .filter(Equipment.id == equipment_id)
        .filter(Equipment.laboratory_id == current_user.laboratory_id)  # ✅ only this lab
        .first()
    )
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(eq, key, value)

    db.commit()
    db.refresh(eq)
    return eq


# --- Delete equipment (in lab) ---
@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("ADMIN", "LAB_TECHNICIAN"):
        raise HTTPException(status_code=403, detail="Not authorized to delete equipment.")

    equipment = (
        db.query(Equipment)
        .filter(Equipment.id == equipment_id)
        .filter(Equipment.laboratory_id == current_user.laboratory_id)  
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    db.delete(equipment)
    db.commit()
    return {"detail": "Deleted successfully"}
