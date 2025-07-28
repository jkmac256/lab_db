#backend/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class RoleEnum(str, Enum):
    DOCTOR = "DOCTOR"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN" 


class UserLogin(BaseModel):
    full_name: str
    password: str
    lab_name: Optional[str] = None  

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum
    laboratory_id: int


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    laboratory_id: Optional[int]

    class Config:
        from_attributes = True

class EquipmentBase(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class EquipmentCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    is_available: bool
    last_serviced: datetime
    added_by_id: int 

class EquipmentOut(BaseModel):
    id: int
    name: str
    type: str
    is_available: bool
    last_serviced: datetime
    description: Optional[str] = None
    added_by: UserOut  

    class Config:
        from_attributes = True

class EquipmentUpdate(BaseModel):
    name: Optional[str]
    type: Optional[str]
    description: Optional[str]
    is_available: Optional[bool]
    last_serviced: Optional[datetime]


class EquipmentSchema(BaseModel):
    id: int
    name: str  # ← this line is crucial
    type: str
    is_available: bool
    last_serviced: datetime
    description: Optional[str] = None

    class Config:
        orm_mode = True


class TestRequestSchema(BaseModel):
    patient_id: int
    patient_name: str
    test_type: str
    equipment_id: int
    technician_id: int

    class Config:
        from_attributes = True


class TestRequestCreate(BaseModel):
    patient_name: str
    patient_dob: date
    patient_gender: str  # ✅ Add this field
    test_type: str
    equipment_name: str
    technician_id: int
    technician_message: Optional[str] = None


class UploadResultsSchema(BaseModel):
    result_details: str  # Details of the test result
    technician_id: int   # Technician ID who is uploading the result
    request_id: int      # Test request ID related to the result

    class Config:
        from_attributes = True


class TestResultSchema(BaseModel):
    id: int
    technician_id: int
    doctor_id: int
    request_id: int
    result_details: str | None = None
    result_file_path: str | None = None
    result_date: datetime
    seen: bool

    class Config:
        from_attributes = True


class DoctorViewTestResult(BaseModel):
    id: int
    result_details: str
    result_date: datetime
    seen: bool
    patient_name: str
    test_type: str
    result_file_path: Optional[str] = None  # ✅ Add this

    class Config:
        from_attributes = True



# --- TestResult schema ---
class TestResultOut(BaseModel):
    id: int
    request_id: int  # match model field name
    technician_id: int  # use technician_id or doctor_id based on your needs
    result_file_path: Optional[str] = None
    result_details: Optional[str] = None
    result_date: datetime  # match model field name

    class Config:
        orm_mode = True  # use orm_mode (preferred in Pydantic v1 and v2)


class TestRequestOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    test_type: str
    equipment: EquipmentOut  
    technician_id: int
    doctor_id: int
    request_date: datetime
    status: str  # pending, seen, completed
    technician_message: Optional[str] = None
    message_for_doctor: Optional[str] = None
    result: Optional[TestResultOut] = None

    class Config:
        from_attributes = True


class TechnicianOut(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        orm_mode = True        


class ShareResultRequest(BaseModel):
    recipient_email: str
    result_id: int
    message: str | None = None


class TestResultAdminOut(BaseModel):
    id: int
    test_request_id: int
    uploaded_by: str           
    result_data: str           
    uploaded_at: datetime      

    class Config:
        from_attributes = True


class TestRequestSummary(BaseModel):
    id: int
    patient_name: str
    test_type: str
    request_date: datetime
    status: str

    class Config:
        from_attributes = True

class TestResultSummary(BaseModel):
    id: int
    request_id: int
    result_details: Optional[str]
    result_date: datetime

    class Config:
        from_attributes = True

class UserDetailOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    laboratory_id: int

    # Optional related data:
    test_requests: Optional[List[TestRequestSummary]] = None
    test_results: Optional[List[TestResultSummary]] = None

    class Config:
        from_attributes = True        


class UserUpdate(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    role: Optional[str]
    laboratory_id: Optional[int]

class PatientOut(BaseModel):
    id: int
    full_name: str
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    medical_records: Optional[str]

    class Config:
        orm_mode = True

class UserDetailOut(UserOut):
    patients: Optional[List[PatientOut]] = []        

class LaboratoryCreate(BaseModel):
    name: str
    address: str
    contact_email: str

class LaboratoryOut(BaseModel):
    id: int
    name: str
    address: str
    contact_email: str

    class Config:
        from_attributes = True       