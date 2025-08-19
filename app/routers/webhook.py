from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from .. import crud, schemas
from ..faq_service import faq_service
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(content=challenge, status_code=200)
    else:
        logger.error("Webhook verification failed.")
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    logger.info(f"Received webhook payload: {payload}")

    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return Response(status_code=200)

        message_data = messages[0]
        whatsapp_id = message_data.get("from")
        message_type = message_data.get("type")

        user = crud.get_or_create_user(db, whatsapp_id=whatsapp_id)

        if message_type == "text":
            content = message_data.get("text", {}).get("body", "")
            crud.create_message(db, message=schemas.MessageCreate(content=content, direction="incoming"), user_id=user.id)
            # Simple trigger for the main menu
            if content.lower() in ["hi", "hello", "menu"]:
                 faq_service.get_greeting_message_and_main_menu(to=whatsapp_id)
            else:
                 faq_service.send_fallback_message(to=whatsapp_id)

        elif message_type == "interactive":
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

            crud.create_message(db, message=schemas.MessageCreate(content=content, direction="incoming", message_type="interactive"), user_id=user.id)

            if selection_id:
                faq_service.process_user_selection(to=whatsapp_id, selection_id=selection_id)
            else:
                faq_service.send_fallback_message(to=whatsapp_id)

        else:
            logger.warning(f"Unsupported message type: {message_type}")

    except (IndexError, KeyError) as e:
        logger.error(f"Error parsing webhook payload: {e}\nPayload: {payload}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    return Response(status_code=200)
