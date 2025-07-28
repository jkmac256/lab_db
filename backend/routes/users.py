from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from dependencies import get_current_user, require_role
from schemas import UserCreate, UserOut, UserDetailOut, UserUpdate
from routes.auth import get_password_hash 
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/technicians/")
def get_technicians(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.User)
        .filter(models.User.role.ilike("TECHNICIAN"))
        .filter(models.User.laboratory_id == current_user.laboratory_id)
        .all()
    )


@router.get("/doctors/")
def get_doctors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.User)
        .filter(models.User.role.ilike("DOCTOR"))
        .filter(models.User.laboratory_id == current_user.laboratory_id)
        .all()
    )


@router.post("/create", response_model=UserOut, dependencies=[Depends(require_role("ADMIN"))])
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists.")

    if user.role.upper() == "ADMIN":
        admin_exists = db.query(models.User).filter(models.User.role == "ADMIN").first()
        if admin_exists:
            raise HTTPException(status_code=403, detail="Only one admin is allowed.")

    hashed_password = get_password_hash(user.password)

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role.upper(),
        laboratory_id=current_user.laboratory_id  # ✅ link to same lab
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=Dict[str, Any])
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.laboratory_id != current_user.laboratory_id:
        raise HTTPException(status_code=403, detail="Access denied: different lab")

    user_data = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }

    if user.role.upper() == "DOCTOR":
        patients = (
            db.query(models.Patient)
            .join(models.TestRequest)
            .filter(models.TestRequest.doctor_id == user.id)
            .all()
        )
        user_data["patients"] = [
            {
                "id": p.id,
                "full_name": p.full_name,
                "dob": str(p.date_of_birth),
                "gender": p.gender,
                "medical_records": p.medical_records
            }
            for p in patients
        ]

        requests = db.query(models.TestRequest).filter(models.TestRequest.doctor_id == user.id).all()
        user_data["test_requests"] = [
            {
                "id": r.id,
                "patient_name": r.patient_name,
                "test_type": r.test_type,
                "status": r.status,
                "requested_at": r.request_date,
            }
            for r in requests
        ]

    elif user.role.upper() == "LAB_TECHNICIAN":
        results = db.query(models.TestResult).filter(models.TestResult.technician_id == user.id).all()
        user_data["test_results"] = [
            {
                "id": res.id,
                "test_request_id": res.request_id,
                "result_details": res.result_details,
                "uploaded_at": res.result_date,
            }
            for res in results
        ]

    return user_data


@router.get("/all/", response_model=List[UserOut], dependencies=[Depends(require_role("ADMIN"))])
def get_all_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(models.User.laboratory_id == current_user.laboratory_id)

    if role:
        query = query.filter(models.User.role.ilike(role))

    return query.all()


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("ADMIN"))])
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.laboratory_id != current_user.laboratory_id:
        raise HTTPException(status_code=404, detail="User not found or access denied")

    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role.upper()

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.laboratory_id != current_user.laboratory_id:
        raise HTTPException(status_code=404, detail="User not found or access denied")

    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}


@router.get("/doctor/test-requests/{doctor_id}", dependencies=[Depends(require_role("ADMIN"))])
def get_test_requests_by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    doctor = db.query(models.User).filter(models.User.id == doctor_id).first()
    if not doctor or doctor.laboratory_id != current_user.laboratory_id:
        raise HTTPException(status_code=403, detail="Access denied: different lab")
    requests = db.query(models.TestRequest).filter(models.TestRequest.doctor_id == doctor_id).all()
    return requests


@router.get("/technician/test-results/{tech_id}", dependencies=[Depends(require_role("ADMIN"))])
def get_test_results_by_technician(
    tech_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tech = db.query(models.User).filter(models.User.id == tech_id).first()
    if not tech or tech.laboratory_id != current_user.laboratory_id:
        raise HTTPException(status_code=403, detail="Access denied: different lab")
    results = db.query(models.TestResult).filter(models.TestResult.technician_id == tech_id).all()
    return results
