# backend/routes/doctor.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from database import get_db
import models
from dependencies import require_role
import schemas
from typing import List
from email.message import EmailMessage
import os
import smtplib
from email_sender import send_mailgun_email

router = APIRouter(prefix="/doctor", tags=["Doctor"])


@router.post("/submit-request/", response_model=schemas.TestRequestOut)
def submit_request(
    request: schemas.TestRequestCreate,
    current_user=Depends(require_role("doctor")),
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.full_name == request.patient_name,
        models.Patient.laboratory_id == current_user.laboratory_id
    ).first()

    if not patient:
        patient = models.Patient(
            full_name=request.patient_name,
            date_of_birth=request.patient_dob,
            gender=request.patient_gender,
            medical_records="",
            laboratory_id=current_user.laboratory_id  # 🔒 tie patient to doctor’s lab
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    equipment = db.query(models.Equipment).filter_by(
        name=request.equipment_name,
        laboratory_id=current_user.laboratory_id  # 🔒 same lab only
    ).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    tr = models.TestRequest(
        patient_id=patient.id,
        patient_name=patient.full_name,
        test_type=request.test_type,
        equipment_id=equipment.id,
        doctor_id=current_user.id,
        technician_id=request.technician_id,
        technician_message=request.technician_message,
        message_for_doctor=None,
        laboratory_id=current_user.laboratory_id  # 🔒 tie request to lab
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)

    return tr


@router.get("/my-requests/")
def view_my_requests(
    current_user=Depends(require_role("doctor")),
    db: Session = Depends(get_db)
):
    requests = (
        db.query(models.TestRequest)
        .options(joinedload(models.TestRequest.equipment))
        .filter_by(
            doctor_id=current_user.id,
            laboratory_id=current_user.laboratory_id  # 🔒 only requests from doctor’s lab
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
            "equipment_name": r.equipment.name if r.equipment else "N/A",
            "technician_id": r.technician_id,
            "status": r.status.value,
        }
        for r in requests
    ]


@router.post("/test-request/{request_id}/message")
def add_message_to_request(
    request_id: int,
    message: str,
    user_role: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["doctor", "technician"]))
):
    request = db.query(models.TestRequest).filter(
        models.TestRequest.id == request_id,
        models.TestRequest.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Test request not found")

    if user_role == "doctor":
        request.message_for_doctor = message
    elif user_role == "technician":
        request.technician_message = message
    else:
        raise HTTPException(status_code=400, detail="Invalid user role")

    db.commit()
    db.refresh(request)
    return {"msg": "Message added successfully", "request_id": request.id}


@router.get("/test-request/{request_id}/messages")
def get_messages_for_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["doctor", "technician"]))
):
    request = db.query(models.TestRequest).filter(
        models.TestRequest.id == request_id,
        models.TestRequest.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Test request not found")

    return {
        "message_for_doctor": request.message_for_doctor,
        "technician_message": request.technician_message
    }


@router.get("/", response_model=List[schemas.TechnicianOut])
def get_all_technicians(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("doctor"))
):
    technicians = db.query(models.User).filter(
        models.User.role.ilike("LAB_TECHNICIAN"),
        models.User.laboratory_id == current_user.laboratory_id  # 🔒 same lab only
    ).all()
    return technicians


@router.get("/test-results/", response_model=List[schemas.DoctorViewTestResult])
def get_test_results_for_doctor(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    results = (
        db.query(models.TestResult)
        .options(joinedload(models.TestResult.test_request).joinedload(models.TestRequest.patient))
        .filter(
            models.TestResult.doctor_id == current_user.id,
            models.TestResult.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
        )
        .all()
    )

    return [
        schemas.DoctorViewTestResult(
            id=result.id,
            result_details=result.result_details,
            result_date=result.result_date,
            seen=result.seen,
            patient_name=result.test_request.patient.full_name,
            test_type=result.test_request.test_type,
            result_file_path=result.result_file_path
        )
        for result in results
    ]


@router.post("/share-result")
def share_result(
    payload: schemas.ShareResultRequest,
    current_user=Depends(require_role("doctor")),
    db: Session = Depends(get_db)
):
    test_result = db.query(models.TestResult).filter(
        models.TestResult.id == payload.result_id,
        models.TestResult.doctor_id == current_user.id,
        models.TestResult.laboratory_id == current_user.laboratory_id  # 🔒 lab scoped
    ).first()

    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found or not owned")

    file_path = test_result.result_file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result file missing")

    try:
        msg = EmailMessage()
        msg["Subject"] = "Medical Lab Test Result"
        msg["From"] = os.getenv("SMTP_SENDER", "medicallabresults@gmail.com")
        msg["To"] = payload.recipient_email
        msg["Reply-To"] = "noreply.medicallabresults@gmail.com"

        msg.set_content(
            (payload.message or "Here is the test result attached.") +
            "\n\nPlease do not reply to this email."
        )

        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
        SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
        SMTP_USER = os.getenv("SMTP_USER")
        SMTP_PASS = os.getenv("SMTP_PASS")

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return {"detail": f"✅ Result shared successfully to {payload.recipient_email}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
