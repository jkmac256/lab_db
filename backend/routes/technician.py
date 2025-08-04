# backend/routes/technician.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import User, TestRequest, TestResult, RequestStatus
from dependencies import get_current_user, require_role
from google.cloud import storage
import os, tempfile, shutil, json, tempfile
from uuid import uuid4
from typing import Optional, List
from schemas import TechnicianOut, UploadResultsSchema, TestResultSchema
from routes.google_cloud import upload_file_to_gcs

GCS_BUCKET_NAME = os.getenv("medicallab-results-bucket")  # ✅ Set this in your env

router = APIRouter(prefix="/technician", tags=["Technician"])

def get_gcs_client():
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("Missing GCS credentials in env var.")

    # Write the JSON to a temp file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp_file:
        temp_file.write(creds_json)
        temp_file_path = temp_file.name

    # Point the Google SDK to this temp file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

    return storage.Client()

@router.post("/upload_result/")
def upload_result(
    request_id: int = Form(...),
    details: str = Form(...),
    result_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ✅ Validate test request ownership
    test_request = db.query(TestRequest).filter(
        TestRequest.id == request_id,
        TestRequest.laboratory_id == current_user.laboratory_id
    ).first()

    if not test_request:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    # ✅ Upload to GCS privately
    try:
        blob_path = upload_file_to_gcs(result_file, request_id, make_public=False)  # update this function!
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {str(e)}")

    # ✅ Save only the blob path in the DB
    new_result = TestResult(
        request_id=request_id,
        technician_id=current_user.id,
        doctor_id=test_request.doctor_id,
        result_details=details,
        result_file_path=blob_path,  # NOT public URL
        seen=False,
        laboratory_id=current_user.laboratory_id
    )
    db.add(new_result)
    test_request.status = RequestStatus.completed

    db.commit()
    db.refresh(new_result)

    return {
        "message": "Result uploaded and request marked as completed",
        "result_id": new_result.id,
        "file_path": blob_path
    }

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
