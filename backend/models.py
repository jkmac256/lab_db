# backend/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy import Enum as SQLAEnum
import enum


class Laboratory(Base):
    __tablename__ = "laboratories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    address = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)

    users = relationship("User", back_populates="laboratory")
    equipment = relationship("Equipment", back_populates="laboratory")
    patients = relationship("Patient", back_populates="laboratory")
    test_requests = relationship("TestRequest", back_populates="laboratory")
    test_results = relationship("TestResult", back_populates="laboratory")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"))
    laboratory = relationship("Laboratory", back_populates="users")

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
    test_requests_sent = relationship(
        "TestRequest",
        back_populates="doctor",
        foreign_keys="TestRequest.doctor_id"
    )
    test_requests_assigned = relationship(
        "TestRequest",
        back_populates="technician",
        foreign_keys="TestRequest.technician_id"
    )


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String)
    is_available = Column(Boolean, default=True)
    last_serviced = Column(DateTime, default=datetime.utcnow)
    description = Column(String)

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"))
    laboratory = relationship("Laboratory", back_populates="equipment")

    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by = relationship("User", back_populates="equipment_added")

    test_requests = relationship("TestRequest", back_populates="equipment")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    medical_records = Column(Text, nullable=True)

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"))
    laboratory = relationship("Laboratory", back_populates="patients")

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

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"))
    laboratory = relationship("Laboratory", back_populates="test_requests")

    patient = relationship("Patient", back_populates="test_requests")
    equipment = relationship("Equipment", back_populates="test_requests")

    doctor = relationship("User", back_populates="test_requests_sent", foreign_keys=[doctor_id])
    technician = relationship("User", back_populates="test_requests_assigned", foreign_keys=[technician_id])

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

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"))
    laboratory = relationship("Laboratory", back_populates="test_results")

    test_request = relationship("TestRequest", back_populates="test_results")
    doctor = relationship("User", back_populates="test_results_received", foreign_keys=[doctor_id])
    technician = relationship("User", back_populates="test_results_uploaded", foreign_keys=[technician_id])
