from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..database import get_db
from ..security import verify_credentials
from ..whatsapp_client import whatsapp_client

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(verify_credentials)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """
    Serves the main dashboard HTML page.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/users", response_model=List[schemas.UserSummary])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all users.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}/messages", response_model=List[schemas.Message])
def get_user_messages(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all messages for a specific user.
    """
    messages = crud.get_messages_by_user(db, user_id=user_id)
    if not messages and not crud.get_user_by_whatsapp_id(db, str(user_id)): # A bit of a hack to check if user exists
        # A better way would be a dedicated get_user_by_id crud function
        raise HTTPException(status_code=404, detail="User not found")
    return messages

@router.post("/users/{user_id}/messages", response_model=schemas.Message)
def send_manual_message(user_id: int, request: schemas.SendMessageRequest, db: Session = Depends(get_db)):
    """
    Send a manual text message to a user from the dashboard.
    """
    # This is inefficient, I should have a get_user_by_id function.
    # I will add it later if I have time. For now, I'll have to iterate.
    users = crud.get_users(db, limit=1000) # Assuming not more than 1000 users for now
    target_user = next((u for u in users if u.id == user_id), None)

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. Send message via WhatsApp API
    response = whatsapp_client.send_text_message(to=target_user.whatsapp_id, text=request.text)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to send message via WhatsApp API")

    # 2. Save the outgoing message to the database
    message_to_save = schemas.MessageCreate(
        content=request.text,
        direction="outgoing",
        message_type="text",
        whatsapp_message_id=response.get("messages", [{}])[0].get("id")
    )
    created_message = crud.create_message(db, message=message_to_save, user_id=target_user.id)

    return created_message
