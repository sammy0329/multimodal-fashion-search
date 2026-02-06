from pydantic import model_validator
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

    # LLM
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.3
    recommend_cache_ttl: int = 3600

    # Pipeline
    clip_batch_size: int = 32
    clip_device: str = ""
    supabase_storage_bucket: str = "product-images"

    @model_validator(mode="after")
    def check_required_keys(self) -> "Settings":
        """프로덕션 환경에서 필수 API 키가 설정되어 있는지 검증한다."""
        if self.app_env == "development":
            return self
        missing = []
        if not self.pinecone_api_key:
            missing.append("PINECONE_API_KEY")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_service_key:
            missing.append("SUPABASE_SERVICE_KEY")
        if missing:
            raise ValueError(f"필수 환경변수 누락: {', '.join(missing)}")
        return self
