# backend/routes/technician.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import User, TestRequest, TestResult, RequestStatus
from dependencies import get_current_user, require_role
import os, json
from typing import Optional, List, Dict, Any
from schemas import TechnicianOut  # you already have this
from routes.google_cloud import upload_file_to_gcs

# 🆕 for middleware preview saving (local Pydantic models to avoid editing schemas.py if you prefer)
from pydantic import BaseModel

class SavePrefilledBody(BaseModel):
    request_id: int
    result_details: Dict[str, Any]          # edited JSON from Streamlit
    result_file_path: Optional[str] = None  # optional if you later render a PDF file on backend

GCS_BUCKET_NAME = os.getenv("medicallab-results-bucket")  # ✅ Set this in your env

router = APIRouter(prefix="/technician", tags=["Technician"])

# ========== MANUAL PATH (unchanged) ==========

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
        blob_path = upload_file_to_gcs(result_file, request_id, make_public=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {str(e)}")

    # ✅ Save only the blob path in the DB
    new_result = TestResult(
        request_id=request_id,
        technician_id=current_user.id,
        doctor_id=test_request.doctor_id,
        result_details=details,            # free text (manual)
        result_file_path=blob_path,        # NOT public URL
        seen=False,
        laboratory_id=current_user.laboratory_id
    )
    db.add(new_result)

    # mark request completed
    test_request.status = RequestStatus.completed

    db.commit()
    db.refresh(new_result)

    return {
        "message": "Result uploaded and request marked as completed",
        "result_id": new_result.id,
        "file_path": blob_path
    }

# ========== AUTOMATIC PATH (preview → edit → save) ==========

# 🆕 1) Fetch from LIS (PREVIEW ONLY) — does NOT write to DB
@router.post("/fetch_from_middleware_preview/")
def fetch_from_middleware_preview(
    request_id: int = Form(...),
    equipment_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("lab_technician")),
):
    # Validate request and lab scoping
    tr = db.query(TestRequest).filter(
        TestRequest.id == request_id,
        TestRequest.laboratory_id == current_user.laboratory_id
    ).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    # Call middleware (online) – preview only
    try:
        from services.middleware_client import fetch_result_from_middleware, MiddlewareError
        preview = fetch_result_from_middleware(request_id, equipment_id)
    except Exception as e:
        # If you want a specific error code for middleware issues:
        raise HTTPException(status_code=502, detail=f"Middleware fetch failed: {str(e)}")

    # Return preview JSON; frontend will render it in an editable form
    return {
        "request_id": request_id,
        "equipment_id": equipment_id,
        "preview": preview
    }

# 🆕 2) Save the EDITED preview as a real TestResult (doctor flow remains unchanged)
@router.post("/save_prefilled_result/")
def save_prefilled_result(
    body: SavePrefilledBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("lab_technician"))
):
    # Validate request & lab scoping
    tr = db.query(TestRequest).filter(
        TestRequest.id == body.request_id,
        TestRequest.laboratory_id == current_user.laboratory_id
    ).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Test request not found or not in your lab")

    # Save edited JSON into the same TestResult table (no new tables/columns)
    new_result = TestResult(
        request_id=body.request_id,
        technician_id=current_user.id,
        doctor_id=tr.doctor_id,
        result_details=json.dumps(body.result_details),  # store edited JSON as text
        result_file_path=body.result_file_path,          # optional (e.g., generated PDF)
        seen=False,
        laboratory_id=current_user.laboratory_id
    )
    db.add(new_result)

    # mark request completed
    tr.status = RequestStatus.completed

    db.commit()
    db.refresh(new_result)

    return {
        "message": "Prefilled result saved and request marked as completed",
        "result_id": new_result.id
    }

# ========== Existing helpers (unchanged) ==========

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
