from typing import Dict, Iterable, List

import json
import logging
import os
import re

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import settings
from ..database import get_db
from ..faq_service import BotMessage, faq_service
from ..whatsapp_client import whatsapp_client

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+")


def _log_bot_messages(db: Session, user_id: int, messages: Iterable[BotMessage]):
    for message in messages:
        crud.create_message(
            db,
            message=schemas.MessageCreate(
                content=message.content,
                direction="outgoing",
                message_type=message.message_type,
                whatsapp_message_id=message.whatsapp_message_id,
            ),
            user_id=user_id,
        )


def _handle_text_message(db: Session, user, message_data: Dict) -> List[BotMessage]:
    message_id = message_data.get("id")
    if message_id and crud.get_message_by_whatsapp_message_id(db, message_id):
        logger.info("Ignoring duplicate text message %s from %s", message_id, user.whatsapp_id)
        return []

    content = message_data.get("text", {}).get("body", "")
    crud.create_message(
        db,
        message=schemas.MessageCreate(
            content=content,
            direction="incoming",
            whatsapp_message_id=message_id,
        ),
        user_id=user.id,
    )

    email_match = EMAIL_REGEX.search(content)
    if email_match:
        email = email_match.group(0)
        return faq_service.handle_desired_email_submission(user.whatsapp_id, email)

    if content.startswith("/"):
        return handle_command(user.whatsapp_id, content)

    lowered = content.lower().strip()
    if lowered in {"hi", "hello", "menu"}:
        return faq_service.get_greeting_message(user.whatsapp_id)

    return faq_service.send_fallback_message(user.whatsapp_id)


def _handle_interactive_message(db: Session, user, message_data: Dict) -> List[BotMessage]:
    message_id = message_data.get("id")
    if message_id and crud.get_message_by_whatsapp_message_id(db, message_id):
        logger.info("Ignoring duplicate interactive message %s from %s", message_id, user.whatsapp_id)
        return []

    interactive_data = message_data.get("interactive", {})
    interaction_type = interactive_data.get("type")

    if interaction_type == "button_reply":
        selection_id = interactive_data.get("button_reply", {}).get("id", "")
        content = interactive_data.get("button_reply", {}).get("title", "")
    elif interaction_type == "list_reply":
        selection_id = interactive_data.get("list_reply", {}).get("id", "")
        content = interactive_data.get("list_reply", {}).get("title", "")
    else:
        selection_id = ""
        content = "Unsupported interactive type"

    crud.create_message(
        db,
        message=schemas.MessageCreate(
            content=content,
            direction="incoming",
            message_type="interactive",
            whatsapp_message_id=message_id,
        ),
        user_id=user.id,
    )

    if selection_id:
        return faq_service.process_user_selection(to=user.whatsapp_id, selection_id=selection_id)

    return faq_service.send_fallback_message(user.whatsapp_id)


def _handle_image_message(db: Session, user, message_data: Dict) -> List[BotMessage]:
    message_id = message_data.get("id")
    if message_id and crud.get_message_by_whatsapp_message_id(db, message_id):
        logger.info("Ignoring duplicate image message %s from %s", message_id, user.whatsapp_id)
        return []

    image_id = message_data.get("image", {}).get("id")
    image_caption = message_data.get("image", {}).get("caption", "")

    if not image_id:
        crud.create_message(
            db,
            message=schemas.MessageCreate(
                content="[Image id missing]",
                direction="incoming",
                message_type="image",
                whatsapp_message_id=message_id,
            ),
            user_id=user.id,
        )
        return faq_service.send_fallback_message(user.whatsapp_id)

    file_name = f"user{user.id}_waimg_{image_id}.jpg"
    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file_name)
    public_url = f"/static/uploads/{file_name}"

    media_url = f"https://graph.facebook.com/{whatsapp_client.API_VERSION}/{image_id}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    try:
        media_resp = requests.get(media_url, headers=headers, timeout=whatsapp_client.REQUEST_TIMEOUT)
        media_resp.raise_for_status()
        media_json = media_resp.json()
        url = media_json.get("url")
        if url:
            img_data = requests.get(url, headers=headers, timeout=whatsapp_client.REQUEST_TIMEOUT)
            img_data.raise_for_status()
            with open(file_path, "wb") as output:
                output.write(img_data.content)
            crud.create_message(
                db,
                message=schemas.MessageCreate(
                    content=public_url,
                    direction="incoming",
                    message_type="image",
                    whatsapp_message_id=message_id,
                ),
                user_id=user.id,
            )
            if image_caption:
                crud.create_message(
                    db,
                    message=schemas.MessageCreate(
                        content=image_caption,
                        direction="incoming",
                    ),
                    user_id=user.id,
                )
        else:
            crud.create_message(
                db,
                message=schemas.MessageCreate(
                    content=f"[Image url missing] {image_caption}",
                    direction="incoming",
                    message_type="image",
                    whatsapp_message_id=message_id,
                ),
                user_id=user.id,
            )
    except requests.RequestException as exc:
        logger.error("Failed to download image %s: %s", image_id, exc)
        crud.create_message(
            db,
            message=schemas.MessageCreate(
                content=f"[Image fetch failed] {image_caption}",
                direction="incoming",
                message_type="image",
                whatsapp_message_id=message_id,
            ),
            user_id=user.id,
        )

    wait_response = whatsapp_client.send_text_message(
        user.whatsapp_id,
        "⏳ *Please wait...* ⏳\n\n> 🔎 Main aapki *payment verify* kar raha hoon.\n> Yeh process sirf kuch seconds lega ✅\n\n🙏 Kripya thoda sabr karein, verification complete hote hi aapko update mil jayega 🚀",
    )
    return [
        BotMessage(
            content="⏳ *Please wait...* ⏳\n\n> 🔎 Main aapki *payment verify* kar raha hoon.\n> Yeh process sirf kuch seconds lega ✅\n\n🙏 Kripya thoda sabr karein, verification complete hote hi aapko update mil jayega 🚀",
            message_type="text",
            whatsapp_message_id=whatsapp_client.extract_message_id(wait_response),
        )
    ]


def handle_command(to: str, command_text: str) -> List[BotMessage]:
    command_text = command_text.lower().strip()
    responses: List[str] = []

    if command_text == "/kara":
        responses.append("It's ABDULLAH CHAUHARY :) ")
    elif command_text == "/help":
        responses.append("Available commands:\n/KARA - About me\n/help - Show menu\n/menu - Show options")
    elif command_text == "/menu":
        return faq_service.get_greeting_message(to)
    else:
        responses.append("Unknown command. Type /help")

    bot_messages: List[BotMessage] = []
    for text in responses:
        response = whatsapp_client.send_text_message(to, text)
        bot_messages.append(
            BotMessage(
                content=text,
                message_type="text",
                whatsapp_message_id=whatsapp_client.extract_message_id(response),
            )
        )
    return bot_messages


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(content=challenge, status_code=200)

    logger.error("Webhook verification failed.")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    logger.info("Received webhook payload: %s", json.dumps(payload, ensure_ascii=False))

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                if not messages:
                    continue

                for message_data in messages:
                    whatsapp_id = message_data.get("from")
                    if not whatsapp_id:
                        logger.warning("Skipping message without sender: %s", message_data)
                        continue

                    user = crud.get_or_create_user(db, whatsapp_id=whatsapp_id)
                    message_type = message_data.get("type")
                    bot_messages: List[BotMessage] = []

                    if message_type == "text":
                        bot_messages = _handle_text_message(db, user, message_data)
                    elif message_type == "interactive":
                        bot_messages = _handle_interactive_message(db, user, message_data)
                    elif message_type == "image":
                        bot_messages = _handle_image_message(db, user, message_data)
                    else:
                        logger.warning("Unsupported message type received: %s", message_type)
                        crud.create_message(
                            db,
                            message=schemas.MessageCreate(
                                content=f"Unsupported message type: {message_type}",
                                direction="incoming",
                            ),
                            user_id=user.id,
                        )
                        bot_messages = faq_service.send_fallback_message(user.whatsapp_id)

                    if bot_messages:
                        _log_bot_messages(db, user.id, bot_messages)

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Error handling webhook: %s", exc)

    return Response(status_code=200)


