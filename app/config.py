from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration settings for the application.

    NOTE: Default values are provided for demonstration purposes in a sandboxed
    environment. In a real production deployment, these should be set using
    actual environment variables or a secure secret management system, not
    hardcoded.
    """

    WHATSAPP_TOKEN: str = "DEFAULT_TOKEN"
    WHATSAPP_PHONE_NUMBER_ID: str = "DEFAULT_PHONE_ID"
    VERIFY_TOKEN: str = "your-secret-verify-token"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "password"
    DATABASE_URL: str = "sqlite:///./whatsapp_faq.db"
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    PROMO_IMAGE_URL: str = "https://via.placeholder.com/600x400.png?text=Promo"
    PROMO_IMAGE_CAPTION: str = "Check out our latest offer!"
    VEO3_INFO_URL: str = "https://www.example.com/veo3"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
