# backend/routes/users.py

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
def get_technicians(db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.role.ilike("TECHNICIAN")).all()


@router.get("/doctors/")
def get_doctors(db: Session = Depends(get_db)):
    return db.query(models.User).filter_by(role="doctor").all()


@router.post("/create", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
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
        role=user.role.upper()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=Dict[str, Any])
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }

    # Get patients that have test requests
    patients = (
        db.query(models.Patient)
        .join(models.TestRequest)
        .filter(models.TestRequest.doctor_id == user.id)
        .all()
        if user.role.upper() == "DOCTOR"
        else []
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

    if user.role.upper() == "DOCTOR":
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


# Get all users with optional role filter (admin only)
@router.get("/all/", response_model=List[UserOut], dependencies=[Depends(require_role("ADMIN"))])
def get_all_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role.ilike(role))
    return query.all()

# Get single user by ID with extended info (admin only)
@router.get("/{user_id}", response_model=UserDetailOut, dependencies=[Depends(require_role("ADMIN"))])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Add extra data if doctor: patients worked on
    patients = []
    if user.role.upper() == "DOCTOR":
        # Assuming you have a way to get patients for this doctor via test requests
        patients_query = (
            db.query(models.Patient)
            .join(models.TestRequest, models.TestRequest.patient_id == models.Patient.id)
            .filter(models.TestRequest.doctor_id == user.id)
            .distinct()
        )
        patients = patients_query.all()

    return UserDetailOut.from_orm(user).copy(update={"patients": patients})

# Update user info (admin only)
@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("ADMIN"))])
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role.upper()

    db.commit()
    db.refresh(user)
    return user

# Delete user (admin only)
@router.delete("/{user_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}

# Get test requests made by doctor (doctor id param)
@router.get("/doctor/test-requests/{doctor_id}", dependencies=[Depends(require_role("ADMIN"))])
def get_test_requests_by_doctor(doctor_id: int, db: Session = Depends(get_db)):
    requests = db.query(models.TestRequest).filter(models.TestRequest.doctor_id == doctor_id).all()
    return requests

# Get test results uploaded by technician (technician id param)
@router.get("/technician/test-results/{tech_id}", dependencies=[Depends(require_role("ADMIN"))])
def get_test_results_by_technician(tech_id: int, db: Session = Depends(get_db)):
    results = db.query(models.TestResult).filter(models.TestResult.technician_id == tech_id).all()
    return results

@router.get("/all/", dependencies=[Depends(require_role("ADMIN"))])
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found")
    return patients