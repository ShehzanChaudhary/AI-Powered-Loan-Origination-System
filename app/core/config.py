from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Stores configuration values required by the application."""
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str

    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    MODEL: str = "openai/gpt-4o-mini"

    credit_bureau_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()

