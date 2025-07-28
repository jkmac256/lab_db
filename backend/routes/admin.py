# backend/routes/admin.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, require_role
from models import User, TestRequest, TestResult
from schemas import RoleEnum, TestRequestOut, TestResultOut, TestResultAdminOut, UserOut, UserDetailOut
from typing import List


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats/total-users")
def get_total_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    count = db.query(User).filter(User.laboratory_id == current_user.laboratory_id).count()
    return {"count": count}


@router.get("/stats/doctors")
def get_total_doctors(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    count = db.query(User).filter(
        User.role == RoleEnum.DOCTOR,
        User.laboratory_id == current_user.laboratory_id
    ).count()
    return {"count": count}


@router.get("/stats/labtechs")
def get_total_labtechs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    count = db.query(User).filter(
        User.role == RoleEnum.LAB_TECHNICIAN,
        User.laboratory_id == current_user.laboratory_id
    ).count()
    return {"count": count}


@router.get("/test-requests", response_model=List[TestRequestOut])
def get_all_test_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(TestRequest).filter(
        TestRequest.laboratory_id == current_user.laboratory_id
    ).all()


@router.get("/test-results/", response_model=List[TestResultAdminOut])
def get_all_results_for_admin(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    results = db.query(TestResult).filter(
        TestResult.laboratory_id == current_user.laboratory_id
    ).all()

    return [
        {
            "id": r.id,
            "test_request_id": r.request_id,
            "uploaded_by": r.technician.full_name if r.technician else "Unknown",
            "result_data": r.result_details,
            "uploaded_at": r.result_date,
        }
        for r in results
    ]


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def get_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(
        User.id == user_id,
        User.laboratory_id == current_user.laboratory_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your lab")
    return user


@router.get("/{user_id}/detail", response_model=UserDetailOut, dependencies=[Depends(require_role("admin"))])
def get_user_detail(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(User).filter(
        User.id == user_id,
        User.laboratory_id == current_user.laboratory_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your lab")

    if user.role.lower() == "doctor":
        test_requests = db.query(TestRequest).filter(
            TestRequest.doctor_id == user.id,
            TestRequest.laboratory_id == current_user.laboratory_id
        ).all()
        return UserDetailOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            test_requests=test_requests,
            test_results=None
        )
    elif user.role.lower() == "lab_technician":
        test_results = db.query(TestResult).filter(
            TestResult.technician_id == user.id,
            TestResult.laboratory_id == current_user.laboratory_id
        ).all()
        return UserDetailOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            test_requests=None,
            test_results=test_results
        )
    else:
        return UserDetailOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role
        )
