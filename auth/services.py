from sqlalchemy.orm import Session
from auth.models import AdminUser
from utils import hash_password, verify_password, create_access_token, decode_token, is_token_blocklisted, add_to_blocklist

class AdminUserService:
    model = AdminUser

    @classmethod
    def get_user_by_email(cls,db: Session, email: str):
        return db.query(cls.model).filter(cls.model.email == email).first()
    
    @classmethod
    def get_by_id(cls, db: Session, model_id: int):
        return db.query(cls.model).filter(cls.model.id == model_id).first()
    
    @classmethod
    def get_all(cls, db: Session, skip: int = 0, limit: int = 100):
        return db.query(cls.model).offset(skip).limit(limit).all()
    
    @classmethod
    def create(cls, db: Session, model_instance):
        db.add(model_instance)
        db.commit()
        db.refresh(model_instance)
        return model_instance