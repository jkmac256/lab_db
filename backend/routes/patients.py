from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from dependencies import get_current_user, require_role

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/all/", dependencies=[Depends(require_role("ADMIN"))])
def get_all_patients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # ✅ Option A: If patients have `laboratory_id` directly
    patients = (
        db.query(models.Patient)
        .filter(models.Patient.laboratory_id == current_user.laboratory_id)
        .all()
    )

    if not patients:
        raise HTTPException(status_code=404, detail="No patients found for your lab")

    return patients
