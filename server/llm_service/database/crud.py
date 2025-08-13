from sqlalchemy.orm import Session
from models import Schedule, Prompt  

def get_all_schedules(db: Session):
    return db.query(Schedule).all()

def get_all_prompts(db: Session):
    return db.query(Prompt).all()
