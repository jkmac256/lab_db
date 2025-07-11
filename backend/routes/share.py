from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import TestRequest, TestResult
from schemas import ShareResultRequest
from dependencies import get_current_user, require_role, get_db
import smtplib
from email.message import EmailMessage
import os

router = APIRouter(prefix="/doctor", tags=["Doctor"])

@router.post("/share-result/", dependencies=[Depends(require_role("doctor"))])
def share_result(payload: ShareResultRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    test_result = db.query(TestResult).filter(TestResult.id == payload.result_id).first()
    if not test_result:
        raise HTTPException(status_code=404, detail="Result not found")

    file_path = test_result.result_file
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result file not found on disk")

    msg = EmailMessage()
    msg["Subject"] = "Test Result"
    msg["From"] = "noreply@medlab.com"
    msg["To"] = payload.recipient_email
    msg.set_content(payload.message or "Please find the attached test result.")

    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)

    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    with smtplib.SMTP("localhost") as server:
        server.send_message(msg)

    return {"detail": f"Result shared with {payload.recipient_email}"}
