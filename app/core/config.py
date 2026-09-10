from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Stores configuration values required by the application."""
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()

