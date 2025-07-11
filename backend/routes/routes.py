# backend/routes/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import TestRequest, User, TestResult
from schemas import TestRequestCreate, TestResultCreate, UploadResultsSchema
from database import get_db
from auth import get_current_user
from dependencies import require_role

@router.get("/only-doctor")
def doctor_data(current_user = Depends(require_role("doctor"))):
    return {"msg": f"Hello Dr. {current_user.name}"}


@app.post("/doctor/submit-request/")
def submit_request(request: TestRequestCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_request = TestRequest(
        patient_name=request.patient_name,
        test_type=request.test_type,
        equipment_id=request.equipment_id,
        doctor_id=current_user["id"],
        technician_id=request.technician_id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return {"message": "Request submitted successfully", "request_id": new_request.id}


@app.post("/technician/upload_result/")
async def upload_result(payload: UploadResultsSchema, db: Session = Depends(get_db)):
    print(f"Received payload: {payload}")

    # Check if the test request exists
    test_request = db.query(TestRequest).filter(TestRequest.id == payload.request_id).first()
    if not test_request:
        raise HTTPException(status_code=404, detail="Test request not found")

    # Check if the technician exists
    technician = db.query(User).filter(User.id == payload.technician_id, User.role == "technician").first()
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")

    # Create test result
    test_result = TestResult(
        request_id=payload.request_id,
        result_details=payload.result_details,
        doctor_id=test_request.doctor_id,  # Linking the doctor from the test request
        technician_id=payload.technician_id
    )

    try:
        db.add(test_result)
        db.commit()
        db.refresh(test_result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload result")

    return {"message": "Result uploaded successfully", "result_id": test_result.id}
