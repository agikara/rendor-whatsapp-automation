import logging
from typing import Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Thin wrapper around the Meta WhatsApp Cloud API."""

    API_VERSION = "v18.0"
    REQUEST_TIMEOUT = 10

    def __init__(self):
        self.api_url = f"https://graph.facebook.com/{self.API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }

    def send_text_message(self, to: str, text: str):
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._send_request(payload)

    def send_interactive_reply_buttons(self, to: str, body_text: str, buttons: list):
        """Send a message with interactive reply buttons."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"]},
                        }
                        for btn in buttons
                    ]
                },
            },
        }
        return self._send_request(payload)

    def send_interactive_list_menu(self, to: str, header_text: str, body_text: str, sections: list):
        """Send a message with an interactive list menu."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header_text},
                "body": {"text": body_text},
                "action": {
                    "button": "View Options",
                    "sections": sections,
                },
            },
        }
        return self._send_request(payload)

    def send_url_button(self, to: str, body_text: str, button_title: str, url: str):
        """Send a single URL button that opens an external website."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "url",
                            "url_button": {
                                "text": button_title[:20],
                                "url": url,
                            },
                        }
                    ]
                },
            },
        }
        return self._send_request(payload)
    def send_media_message(
        self,
        to: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ):
        """Send an image or document message using a publicly accessible link."""
        if media_type not in {"image", "document"}:
            raise ValueError("media_type must be either 'image' or 'document'")

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": media_type,
            media_type: {"link": media_url},
        }

        if caption:
            payload[media_type]["caption"] = caption
        if media_type == "document" and filename:
            payload[media_type]["filename"] = filename

        return self._send_request(payload)

    def _send_request(self, payload: dict):
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            logger.info(
                "Message sent successfully to %s. Response: %s",
                payload.get("to"),
                response.json(),
            )
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Error sending message: %s", exc)
            if exc.response is not None:
                try:
                    logger.error("Response body: %s", exc.response.json())
                except ValueError:
                    logger.error("Response body: %s", exc.response.text)
            return None

    @staticmethod
    def extract_message_id(response_json: Optional[dict]) -> Optional[str]:
        """Safely pull the WhatsApp message id from an API response."""
        if not response_json:
            return None
        messages = response_json.get("messages")
        if not messages:
            return None
        first_message = messages[0]
        if not isinstance(first_message, dict):
            return None
        return first_message.get("id")


whatsapp_client = WhatsAppClient()



