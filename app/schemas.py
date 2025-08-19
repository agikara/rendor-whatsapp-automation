from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Message Schemas
class MessageBase(BaseModel):
    content: str
    direction: str
    message_type: str = "text"
    whatsapp_message_id: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Dashboard Schemas
class SendMessageRequest(BaseModel):
    text: str

# User Schemas
class UserBase(BaseModel):
    whatsapp_id: str

class UserCreate(UserBase):
    pass

class UserSummary(UserBase):
    id: int

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    created_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True
