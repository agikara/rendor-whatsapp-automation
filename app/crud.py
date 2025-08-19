from sqlalchemy.orm import Session
from . import models, schemas

def get_user_by_whatsapp_id(db: Session, whatsapp_id: str):
    """
    Retrieve a user by their WhatsApp ID.
    """
    return db.query(models.User).filter(models.User.whatsapp_id == whatsapp_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    Create a new user.
    """
    db_user = models.User(whatsapp_id=user.whatsapp_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, whatsapp_id: str):
    """
    Get a user by WhatsApp ID, or create them if they don't exist.
    """
    db_user = get_user_by_whatsapp_id(db, whatsapp_id=whatsapp_id)
    if not db_user:
        db_user = create_user(db, user=schemas.UserCreate(whatsapp_id=whatsapp_id))
    return db_user

def create_message(db: Session, message: schemas.MessageCreate, user_id: int):
    """
    Create a new message and associate it with a user.
    """
    db_message = models.Message(**message.model_dump(), user_id=user_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve all users.
    """
    return db.query(models.User).offset(skip).limit(limit).all()

def get_messages_by_user(db: Session, user_id: int):
    """
    Retrieve all messages for a specific user, ordered by timestamp.
    """
    return db.query(models.Message).filter(models.Message.user_id == user_id).order_by(models.Message.timestamp.asc()).all()
