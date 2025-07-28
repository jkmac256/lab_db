from sqlalchemy.orm import Session
import models
import schemas

def create_lab(db: Session, lab_in: schemas.LaboratoryCreate):
    db_lab = models.Laboratory(**lab_in.dict())
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab

def get_lab_by_name(db: Session, name: str):
    return db.query(models.Laboratory).filter(models.Laboratory.name == name).first()
