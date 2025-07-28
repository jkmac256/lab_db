# backend/routes/technician.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import User, TestRequest, TestResult, RequestStatus
from dependencies import require_role, get_current_user
from schemas import UploadResultsSchema, TestResultSchema
import os, shutil
from uuid import uuid4
from typing import List
from schemas import TechnicianOut

router = APIRouter(prefix="/technician", tags=["Technician"])
UPLOAD_DIR = "uploaded_results"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(upload_file):
    filename = f"{uuid4().hex}_{upload_file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())

    return file_path


@router.get("/pending-requests/")
def get_pending_requests(
    current_user=Depends(require_role("lab_technician")),
    db: Session = Depends(get_db)
):
    requests = (
        db.query(TestRequest)
        .options(joinedload(TestRequest.equipment))
        .filter(
            TestRequest.technician_id == current_user.id,
            TestRequest.status == RequestStatus.pending,
            TestRequest.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
        )
        .all()
    )

    return [
        {
            "id": r.id,
            "patient_name": r.patient_name,
            "test_type": r.test_type,
            "request_date": r.request_date,
            "equipment_id": r.equipment_id,
            "equipment_name": r.equipment.name if r.equipment else "Unknown",
            "doctor_id": r.doctor_id,
            "status": r.status.value,
        }
        for r in requests
    ]


@router.post("/upload_result/")
def upload_result(
    request_id: int = Form(...),
    details: str = Form(...),
    result_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch and validate test request with lab scope
    test_request = db.query(TestRequest).filter(
        TestRequest.id == request_id,
        TestRequest.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
    ).first()
    if not test_request:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    # Save uploaded file
    upload_folder = os.path.abspath(UPLOAD_DIR)
    os.makedirs(upload_folder, exist_ok=True)
    filename = result_file.filename.replace(" ", "_")
    file_path = os.path.join(upload_folder, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(result_file.file, f)

    # Create TestResult tied to lab
    new_result = TestResult(
        request_id=request_id,
        technician_id=current_user.id,
        doctor_id=test_request.doctor_id,
        result_details=details,
        result_file_path=file_path,
        seen=False,
        laboratory_id=current_user.laboratory_id  # 🔒 lab tied
    )
    db.add(new_result)

    # Update test request status to completed
    test_request.status = RequestStatus.completed

    db.commit()
    db.refresh(new_result)

    return {
        "message": "Result uploaded and request marked as completed",
        "result_id": new_result.id
    }


@router.get("/test-request/{request_id}/messages")
def get_messages_for_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("lab_technician"))
):
    request = db.query(TestRequest).filter(
        TestRequest.id == request_id,
        TestRequest.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    return {
        "message_for_doctor": request.message_for_doctor,
        "technician_message": request.technician_message
    }


@router.get("/technicians/", response_model=List[TechnicianOut])
def get_all_technicians(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("lab_technician"))
):
    technicians = db.query(User).filter(
        User.role.ilike("LAB_TECHNICIAN"),
        User.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped list
    ).all()
    return technicians
