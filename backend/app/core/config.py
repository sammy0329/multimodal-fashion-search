from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_version: str = "0.1.0"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # AI
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index: str = "style-matcher"

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"
