import json
import logging
from .whatsapp_client import whatsapp_client

logger = logging.getLogger(__name__)

class FaqService:
    def __init__(self, faq_path="faq.json"):
        try:
            with open(faq_path, "r") as f:
                self.faq_data = json.load(f)
            logger.info("FAQ data loaded successfully.")
        except FileNotFoundError:
            logger.error(f"FAQ file not found at {faq_path}")
            self.faq_data = {}
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {faq_path}")
            self.faq_data = {}

    def get_greeting_message_and_main_menu(self, to: str):
        """Sends the initial greeting and the main menu."""
        greeting = self.faq_data.get("greeting", "Hello!")
        whatsapp_client.send_text_message(to, greeting)

        main_menu_data = self.faq_data.get("main_menu")
        if main_menu_data:
            self.send_list_menu(to, main_menu_data)

    def process_user_selection(self, to: str, selection_id: str):
        """Processes a user's selection from an interactive menu."""
        if selection_id == "main_menu":
            self.get_greeting_message_and_main_menu(to)
            return

        # Search for the selection in all menus
        for menu_key, menu_data in self.faq_data.get("menus", {}).items():
            for option in menu_data.get("options", []):
                if option["id"] == selection_id:
                    action = option.get("action")
                    if action:
                        self.execute_action(to, action)
                    else: # It's a submenu
                        submenu_data = self.faq_data.get("menus", {}).get(selection_id)
                        if submenu_data:
                            self.send_list_menu(to, submenu_data)
                        else:
                            self.send_fallback_message(to)
                    return

        # If the id corresponds to a main menu category that opens a submenu
        main_menu_options = {opt["id"] for opt in self.faq_data.get("main_menu", {}).get("options", [])}
        if selection_id in main_menu_options:
             submenu_data = self.faq_data.get("menus", {}).get(selection_id)
             if submenu_data:
                self.send_list_menu(to, submenu_data)
                return

        self.send_fallback_message(to)

    def execute_action(self, to: str, action: dict):
        action_type = action.get("type")
        body = action.get("body", "Sorry, something went wrong.")

        if action_type == "reply":
            whatsapp_client.send_text_message(to, body)
        # TODO: Implement CTA actions if they are defined in faq.json
        # For now, just sending the text part.
        elif action_type in ["cta_call", "cta_url"]:
             whatsapp_client.send_text_message(to, body)
        else:
            self.send_fallback_message(to)

    def send_list_menu(self, to: str, menu_data: dict):
        title = menu_data.get("title", "Menu")
        body = menu_data.get("body", "Please choose an option.")
        options = menu_data.get("options", [])

        if not options:
            whatsapp_client.send_text_message(to, "Sorry, there are no options available in this category yet.")
            return

        # WhatsApp List Menus require at least one section
        sections = [{
            "title": title,
            "rows": [
                {"id": opt["id"], "title": opt["title"]} for opt in options
            ]
        }]
        whatsapp_client.send_interactive_list_menu(to, title, body, sections)

    def send_fallback_message(self, to: str):
        fallback_msg = self.faq_data.get("fallback", {}).get("body", "Sorry, I didn't understand.")
        whatsapp_client.send_text_message(to, fallback_msg)


faq_service = FaqService()
