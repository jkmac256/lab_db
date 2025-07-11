# backend/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy import Enum as SQLAEnum
import enum


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

    equipment_added = relationship("Equipment", back_populates="added_by")

    test_results_uploaded = relationship(
        "TestResult",
        back_populates="technician",
        foreign_keys="TestResult.technician_id"
    )
    test_results_received = relationship(
        "TestResult",
        back_populates="doctor",
        foreign_keys="TestResult.doctor_id"
    )


class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String)
    is_available = Column(Boolean, default=True)
    last_serviced = Column(DateTime, default=datetime.utcnow)
    description = Column(String)

    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by = relationship("User", back_populates="equipment_added")



class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    medical_records = Column(Text, nullable=True)

    test_requests = relationship("TestRequest", back_populates="patient")


class RequestStatus(str, enum.Enum):
    pending = "pending"
    seen = "seen"
    completed = "completed"



class TestRequest(Base):
    __tablename__ = "test_requests"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient_name = Column(String, nullable=False)
    test_type = Column(String)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    technician_id = Column(Integer, ForeignKey("users.id"))
    request_date = Column(DateTime, default=datetime.utcnow)
    technician_message = Column(Text, nullable=True)
    message_for_doctor = Column(Text, nullable=True)
    status = Column(SQLAEnum(RequestStatus), default=RequestStatus.pending)

    patient = relationship("Patient", back_populates="test_requests")
    technician = relationship("User", foreign_keys=[technician_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    equipment = relationship("Equipment")
    test_results = relationship("TestResult", back_populates="test_request", uselist=False)


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("test_requests.id"))
    result_details = Column(Text)
    result_date = Column(DateTime, default=datetime.utcnow)
    result_file_path = Column(String, nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    technician_id = Column(Integer, ForeignKey("users.id"))
    seen = Column(Boolean, default=False)

    test_request = relationship("TestRequest", back_populates="test_results")
    technician = relationship("User", foreign_keys=[technician_id])
    doctor = relationship("User", foreign_keys=[doctor_id])


