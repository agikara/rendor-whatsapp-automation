import requests
import logging
from .config import settings

logger = logging.getLogger(__name__)

class WhatsAppClient:
    API_URL = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    HEADERS = {
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
        """
        Send a message with interactive reply buttons.
        buttons: A list of dicts, e.g., [{"id": "btn1", "title": "Button 1"}]
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                        for btn in buttons
                    ]
                },
            },
        }
        return self._send_request(payload)

    def send_interactive_list_menu(self, to: str, header_text: str, body_text: str, sections: list):
        """
        Send a message with an interactive list menu.
        sections: A list of dicts, e.g., [{"title": "Section 1", "rows": [{"id": "row1", "title": "Row 1"}]}]
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header_text},
                "body": {"text": body_text},
                "action": {
                    "button": "View Options", # The text on the button that opens the list
                    "sections": sections
                },
            },
        }
        return self._send_request(payload)

    def _send_request(self, payload: dict):
        try:
            response = requests.post(self.API_URL, json=payload, headers=self.HEADERS)
            response.raise_for_status()
            logger.info(f"Message sent successfully to {payload['to']}. Response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
            return None

whatsapp_client = WhatsAppClient()
