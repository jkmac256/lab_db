from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, models
from dependencies import get_db, get_current_active_user

router = APIRouter()

@router.post("/labs/", response_model=schemas.LaboratoryInDB)
def create_lab(
    lab_in: schemas.LaboratoryCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")

    existing_lab = crud.get_lab_by_name(db, lab_in.name)
    if existing_lab:
        raise HTTPException(status_code=400, detail="Lab name already exists")

    return crud.create_lab(db, lab_in)
