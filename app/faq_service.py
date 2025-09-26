import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .config import settings
from .whatsapp_client import whatsapp_client

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "🎉 *Welcome to Google AI Pro!* 🎉\n\n"
    "Hello 👋,\n"
    "Aapka swagat hai! 🤗\n"
    "Hum khush hain ke aap humare AI family ka hissa bane ho 🌟.\n\n"
    "✨ Yahaan aapko milega ek naya experience jo aapke din ko banayega aur bhi productive & exciting 🚀.\n\n"
    "🙏 Shukriya hum par trust karne ke liye —\n"
    "Let’s start this amazing journey together! 💡"
)

OFFER_MESSAGE = (
    "🔥 *Google AI Pro – Special Offer!* 🔥\n\n"
    "> 🚀 Upgrade your world with *Google AI Pro*\n"
    "> 🧠 Smarter • 🎬 Creative • 📈 Productive\n\n"
    "💰 *Price:*\n"
    "✨ Only *999 PKR* 🇵🇰\n"
    "✨ Just *$3.5* 🌍\n\n"
    "🌟 *Why choose Google AI Pro?*\n"
    "✅ Ultra-fast & powerful AI\n"
    "✅ Smart personal assistant 🤖\n"
    "✅ Boost creativity, research & productivity\n\n"
    "🎉 *Limited Time Offer – Don’t Miss Out!* 🎉\n\n"
    "👉 Abhi join karein aur AI ka next-level experience hasil karein!"
)

BUY_MESSAGE = (
    "🎉 *Great Choice!* 🎉\n\n"
    "🙌 Aapne *Google Veo 3 Offer* select kiya hai!\n\n"
    "> ✨ Ab sirf ek step baqi hai...\n"
    "> Chuno apna *Desired Email* ya le lo ek *Random Email*.\n\n"
    "👇 Select one to continue:\n"
    "✅ *Desired Email* — apna pasandida email choose karo\n"
    "🎲 *Random Email* — system aapko ek email dega\n"
    "🧑‍💻 *Talk to a Human* — support team se baat karo\n\n"
    "🚀 *Hurry up!* Abhi choose karein aur apna AI access turant unlock karein 🔑"
)

DESIRED_EMAIL_PROMPT = (
    "📧 *Enter Your Desired Email* 📧\n\n"
    "> 👉 Kripya apna *complete email address* type karein:\n"
    "> (Example: _yourname@gmail.com_)\n\n"
    "✨ *Tips:*\n"
    "> • Apna koi bhi *email alias/name* de dein\n"
    "> • Main aapke diye gaye name ka ek *fresh Gmail* bana kar ye offer laga dunga 🚀"
)

RANDOM_EMAIL_MESSAGE = (
    "🎲 *Random Email Selected!* 🎲\n\n"
    "> ✅ No problem!\n"
    "> Hum aapke liye ek *random email* generate kar denge."
)

PAYMENT_PROMPT = (
    "💳 *Please select your payment option:*\n\n"
    "> 🏦 Meezan Bank\n"
    "> 💸 SadaPay\n"
    "> 🌍 Binance"
)

PAYMENT_DETAILS: Dict[str, str] = {
    "payment_meezan": (
        "🏦 *Meezan Bank – Payment Details* 🏦\n\n"
        "> 👤 *Account Title:* ABDULLAH CHAUDHARY\n"
        "> 🔢 *Account Number:* 00300112023010\n"
        "> 🌐 *IBAN:* PK74MEZN0000300112023010\n\n"
        "✅ After payment, kripya apna *screenshot* send karein for verification 📷"
    ),
    "payment_sadapay": (
        "💸 *SadaPay – Payment Details* 💸\n\n"
        "> 👤 *Account Title:* ABDULLAH CHAUDHARY\n"
        "> 🔢 *Account Number:* 0344-3777775\n\n\n"
        "💸 *NayaPay – Payment Details* 💸\n\n"
        "> 👤 *Account Title:* ABDULLAH CHAUDHARY\n"
        "> 🔢 *Account Number:* 0344-3777775\n\n"
        "✅ After payment, kripya apna *screenshot* send karein for verification 📷"
    ),
    "payment_binance": (
        "🌍 *Binance – Payment Details* 🌍\n\n"
        "> 👤 *Account Name:* An Error Occured , Please select another payment method\n"
        "> 🪙 *USDT (TRC20) Wallet Address:* XXXXXXXXXXXXXXXXXXXXX\n\n"
        "✅ After payment, kripya apna *transaction screenshot* send karein for verification 📷"
    ),
}

EMAIL_REGEX = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+")


@dataclass
class BotMessage:
    content: str
    message_type: str = "text"
    whatsapp_message_id: Optional[str] = None


class FaqService:
    def __init__(self, faq_path: str = "faq.json"):
        try:
            with open(faq_path, "r", encoding="utf-8") as handle:
                self.faq_data = json.load(handle)
            logger.info("FAQ data loaded successfully.")
        except FileNotFoundError:
            logger.error("FAQ file not found at %s", faq_path)
            self.faq_data = {}
        except json.JSONDecodeError:
            logger.error("Error decoding JSON from %s", faq_path)
            self.faq_data = {}

    def get_greeting_message(self, to: str) -> List[BotMessage]:
        messages: List[BotMessage] = []

        messages.append(self._send_text(to, WELCOME_MESSAGE))
        messages.append(self._send_text(to, OFFER_MESSAGE))

        promo_message = self._send_promo_image(to)
        if promo_message:
            messages.append(promo_message)

        offer_text = "Choose an option below to continue."
        buttons = [
            {"id": "veo3_buy", "title": "Buy This"},
            {"id": "veo3_info", "title": "More Info"},
            {"id": "veo3_talk_human", "title": "Talk to a Human"},
        ]
        messages.extend(self._send_reply_buttons(to, offer_text, buttons))

        return messages

    def process_user_selection(self, to: str, selection_id: str) -> List[BotMessage]:
        if selection_id == "veo3_buy":
            messages = [self._send_text(to, BUY_MESSAGE)]
            buttons = [
                {"id": "veo3_email_desired", "title": "Desired Email"},
                {"id": "veo3_email_random", "title": "Random Email"},
                {"id": "veo3_talk_human", "title": "Talk to a Human"},
            ]
            messages.extend(self._send_reply_buttons(to, "Select one option to continue:", buttons))
            return messages

        if selection_id == "veo3_info":
            messages: List[BotMessage] = [
                self._send_text(
                    to,
                    "🔹 *Google AI Pro – Features Summary* 🔹\n\n"
                    "🧠 *Advanced Features*:\n"
                    "✨ *Gemini 2.5 Pro* model access  \n"
                    "🔍 *Deep Research* mode  \n"
                    "🎬 *Video generation* via _Veo 3 Fast_  \n"
                    "🎥 *Flow* — AI filmmaking tool  \n"
                    "🖼️ *Whisk* — image-to-video creation  \n"
                    "🤖 *Jules Agent* — personal AI assistant for planning, tasks & guidance  \n"
                    "📧 *Integration* with Gmail, Docs, Sheets, Slides, Chrome  \n"
                    "📝 *NotebookLM* — smart notes & research support  \n"
                    "💾 *2 TB storage* (Drive / Gmail / Photos)  \n"
                    "🎟️ *Monthly AI Credits* for image/video use  \n"
                    "📈 *Higher limits* on prompts, context, etc.  \n\n"
                    "⚖️ *Free vs Pro*:\n"
                    "🙅‍♂️ _Free users_ → limited prompts & restricted model access  \n"
                    "✅ _Pro users_ → unlimited features, higher usage, priority updates  \n\n"
                    "⚠️ *Notes*:\n"
                    "🌎 Kuch features region-specific (US)  \n"
                    "⏳ Usage limits / caps har feature pe hain  \n"
                    "🚀 Kuch advanced modes (jaise *Deep Think*) future mein aayenge",
                )
            ]
            promo_message = self._send_promo_image(to)
            if promo_message:
                messages.append(promo_message)

            url_button = self._send_url_button(
                to,
                "For a deep dive into Google Veo 3, tap below.",
                "More Info",
                settings.VEO3_INFO_URL,
            )
            if url_button:
                messages.append(url_button)
            return messages

        if selection_id == "veo3_talk_human":
            return [
                self._send_text(
                    to,
                    "A human agent will contact you soon. Thank you!",
                )
            ]

        if selection_id == "veo3_email_desired":
            return [self._send_text(to, DESIRED_EMAIL_PROMPT)]

        if selection_id == "veo3_email_random":
            messages = [self._send_text(to, RANDOM_EMAIL_MESSAGE)]
            messages.extend(self._send_payment_options(to))
            return messages

        if selection_id in PAYMENT_DETAILS:
            return [self._send_text(to, PAYMENT_DETAILS[selection_id])]

        return self.send_fallback_message(to)

    def handle_desired_email_submission(self, to: str, email: str) -> List[BotMessage]:
        messages = [
            self._send_text(
                to,
                f"✅ I received your desired email: {email}\nWe'll use this for your Google Veo 3 delivery.",
            )
        ]
        messages.extend(self._send_payment_options(to))
        return messages

    def send_fallback_message(self, to: str) -> List[BotMessage]:
        fallback_msg = self.faq_data.get(
            "fallback",
            {}).get(
            "body",
            "🤔 *Sorry, I didn’t get that.*\n  > Please choose an option or type *'menu'* 📋",
        )
        return [self._send_text(to, fallback_msg)]

    def _send_payment_options(self, to: str) -> List[BotMessage]:
        messages = [self._send_text(to, PAYMENT_PROMPT)]
        buttons = [
            {"id": "payment_meezan", "title": "Meezan Bank"},
            {"id": "payment_sadapay", "title": "SadaPay / NayaPay"},
            {"id": "payment_binance", "title": "Binance"},
        ]
        messages.extend(self._send_reply_buttons(to, "Select an option below:", buttons))
        return messages

    def _send_promo_image(self, to: str) -> Optional[BotMessage]:
        image_url = settings.PROMO_IMAGE_URL.strip()
        if not image_url:
            return None
        caption = settings.PROMO_IMAGE_CAPTION.strip() or None
        return self._send_image(to, image_url, caption)

    def _send_text(self, to: str, text: str) -> BotMessage:
        response = whatsapp_client.send_text_message(to, text)
        return BotMessage(
            content=text,
            message_type="text",
            whatsapp_message_id=whatsapp_client.extract_message_id(response),
        )

    def _send_reply_buttons(self, to: str, body_text: str, buttons: List[Dict[str, str]]) -> List[BotMessage]:
        response = whatsapp_client.send_interactive_reply_buttons(to, body_text, buttons)
        formatted = self._format_buttons_message(body_text, buttons)

        if response:
            return [
                BotMessage(
                    content="[Interactive buttons]\n" + formatted,
                    message_type="interactive",
                    whatsapp_message_id=whatsapp_client.extract_message_id(response),
                )
            ]

        logger.warning("Interactive buttons failed for %s; falling back to text", to)
        return [self._send_text(to, formatted)]

    def _send_url_button(self, to: str, body_text: str, button_title: str, url: str) -> Optional[BotMessage]:
        response = whatsapp_client.send_url_button(to, body_text, button_title, url)
        if response:
            summary = f"[URL button] {button_title} -> {url}"
            return BotMessage(
                content=summary,
                message_type="interactive",
                whatsapp_message_id=whatsapp_client.extract_message_id(response),
            )
        logger.warning("Failed to send URL button to %s", to)
        return None

    def _send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> Optional[BotMessage]:
        if not image_url:
            return None
        response = whatsapp_client.send_media_message(
            to=to,
            media_type="image",
            media_url=image_url,
            caption=caption,
        )
        if response:
            content = caption or image_url
            return BotMessage(
                content=content,
                message_type="image",
                whatsapp_message_id=whatsapp_client.extract_message_id(response),
            )
        logger.warning("Failed to send image to %s", to)
        return None

    @staticmethod
    def _format_buttons_message(body_text: str, buttons: List[Dict[str, str]]) -> str:
        button_lines = [f"- {button['title']}" for button in buttons]
        parts = [body_text.strip(), "", "Options:"] + button_lines
        return "\n".join(line for line in parts if line)


faq_service = FaqService()
