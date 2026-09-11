from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Stores configuration values required by the application."""
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str

    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    MODEL: str = "openai/gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()

