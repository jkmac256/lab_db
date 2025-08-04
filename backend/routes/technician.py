# backend/routes/technician.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestRequest, TestResult, RequestStatus
from dependencies import get_current_user
from google.cloud import storage
import os, tempfile, uuid
from typing import Optional

router = APIRouter(prefix="/technician", tags=["Technician"])

# Replace with your actual GCS bucket name
GCS_BUCKET_NAME = "your-gcs-bucket-name"

def get_gcs_client():
    credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not credentials_json:
        raise RuntimeError("Missing GCS credentials in env var.")

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp:
        temp.write(credentials_json)
        temp.flush()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp.name

    return storage.Client()

def upload_file_to_gcs(file: UploadFile, request_id: int) -> str:
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET_NAME)

    unique_filename = f"{request_id}_{uuid.uuid4().hex}_{file.filename.replace(' ', '_')}"
    blob = bucket.blob(f"results/{unique_filename}")

    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()  # Optional: remove if using signed URLs

    return blob.public_url

@router.post("/upload_result/")
def upload_result(
    request_id: int = Form(...),
    details: str = Form(...),
    result_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ✅ Validate test request belongs to technician's lab
    test_request = db.query(TestRequest).filter(
        TestRequest.id == request_id,
        TestRequest.laboratory_id == current_user.laboratory_id
    ).first()

    if not test_request:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    # ✅ Upload file to GCS
    try:
        public_url = upload_file_to_gcs(result_file, request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {str(e)}")

    # ✅ Create TestResult with GCS file link
    new_result = TestResult(
        request_id=request_id,
        technician_id=current_user.id,
        doctor_id=test_request.doctor_id,
        result_details=details,
        result_file_path=public_url,
        seen=False,
        laboratory_id=current_user.laboratory_id
    )
    db.add(new_result)

    # ✅ Mark test request as completed
    test_request.status = RequestStatus.completed

    db.commit()
    db.refresh(new_result)

    return {
        "message": "Result uploaded and request marked as completed",
        "result_id": new_result.id,
        "file_url": public_url
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
