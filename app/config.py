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

    class Config:
        # The settings will first try to load from a .env file if it exists,
        # otherwise it will use the default values defined above.
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
