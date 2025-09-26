from __future__ import annotations

import re
import time
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import settings
from ..database import get_db
from ..security import verify_credentials
from ..whatsapp_client import whatsapp_client

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(verify_credentials)],
)

templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _build_public_url(filename: str) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/static/uploads/{filename}"


def _sanitize_filename(filename: str) -> str:
    basename = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", basename)


@router.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "dashboard_title": "WhatsApp Chat Desk",
        },
    )


@router.get("/users", response_model=List[schemas.UserSummary])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}/messages", response_model=List[schemas.Message])
def get_user_messages(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    messages = crud.get_messages_by_user(db, user_id=user_id)
    return messages


@router.post("/users/{user_id}/messages", response_model=schemas.Message)
def send_manual_message(
    user_id: int,
    payload: schemas.SendMessageRequest,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty.",
        )

    response = whatsapp_client.send_text_message(to=user.whatsapp_id, text=text)
    message = schemas.MessageCreate(
        content=text,
        direction="outgoing",
        message_type="text",
        whatsapp_message_id=whatsapp_client.extract_message_id(response),
    )
    return crud.create_message(db, message=message, user_id=user.id)


@router.post("/users/{user_id}/files", response_model=schemas.Message)
async def send_file_message(
    user_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    sanitized_name = _sanitize_filename(file.filename or "upload")
    suffix = Path(sanitized_name).suffix
    timestamp = int(time.time())
    stored_filename = f"user{user_id}_{timestamp}{suffix}"
    destination = UPLOAD_DIR / stored_filename

    async with aiofiles.open(destination, "wb") as buffer:
        contents = await file.read()
        await buffer.write(contents)

    relative_url = f"/static/uploads/{stored_filename}"
    public_url = _build_public_url(stored_filename)
    trimmed_caption = caption.strip() if caption else None

    if file.content_type and file.content_type.startswith("image/"):
        message_type = "image"
        response = whatsapp_client.send_media_message(
            to=user.whatsapp_id,
            media_type="image",
            media_url=public_url,
            caption=trimmed_caption,
        )
    else:
        message_type = "document"
        response = whatsapp_client.send_media_message(
            to=user.whatsapp_id,
            media_type="document",
            media_url=public_url,
            caption=trimmed_caption,
            filename=sanitized_name,
        )

    saved_message = crud.create_message(
        db,
        message=schemas.MessageCreate(
            content=relative_url,
            direction="outgoing",
            message_type=message_type,
            whatsapp_message_id=whatsapp_client.extract_message_id(response),
        ),
        user_id=user.id,
    )

    if trimmed_caption:
        crud.create_message(
            db,
            message=schemas.MessageCreate(
                content=trimmed_caption,
                direction="outgoing",
            ),
            user_id=user.id,
        )

    return saved_message
