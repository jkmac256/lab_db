from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import TestRequest, User, TestResult
from schemas import TestRequestCreate, UploadResultsSchema
from database import get_db
from dependencies import get_current_user, require_role

router = APIRouter(prefix="", tags=["Core"])

# ✅ Doctor-only test route
@router.get("/only-doctor")
def doctor_data(current_user=Depends(require_role("doctor"))):
    return {"msg": f"Hello Dr. {current_user.full_name}"}


# ✅ Doctor submits request — must match lab
@router.post("/doctor/submit-request/")
def submit_request(
    request: TestRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    # OPTIONAL: Validate that equipment & technician are in same lab if needed

    new_request = TestRequest(
        patient_name=request.patient_name,
        test_type=request.test_type,
        equipment_id=request.equipment_id,
        doctor_id=current_user.id,
        technician_id=request.technician_id,
        # Add lab if your model has: laboratory_id=current_user.laboratory_id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return {"message": "Request submitted successfully", "request_id": new_request.id}


# ✅ Technician uploads result — must match lab
@router.post("/technician/upload_result/")
async def upload_result(
    payload: UploadResultsSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("lab_technician"))
):
    # Confirm test request exists & belongs to same lab
    test_request = db.query(TestRequest).filter(TestRequest.id == payload.request_id).first()
    if not test_request:
        raise HTTPException(status_code=404, detail="Test request not found")

    # Create test result linked to same doctor & lab
    test_result = TestResult(
        request_id=payload.request_id,
        result_details=payload.result_details,
        doctor_id=test_request.doctor_id,
        technician_id=current_user.id,
        # Add lab if your model has: laboratory_id=current_user.laboratory_id
    )

    try:
        db.add(test_result)
        db.commit()
        db.refresh(test_result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload result")

    return {"message": "Result uploaded successfully", "result_id": test_result.id}
