from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Twilio Configuration
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    public_url: str

    # Audio Processing
    silence_threshold_seconds: float = 4.0
    audio_sample_rate: int = 8000

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    session_ttl: int = 3600  # 1 hour

    # Chroma Configuration
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "company_knowledge"

    # Gemini Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 500

    # RAG Configuration
    rag_top_k: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50

    # Concurrency Configuration
    max_concurrent_calls: int = 100
    worker_pool_size: int = 20
    request_timeout: int = 30

    # Feature Flags
    enable_rag: bool = True
    enable_redis: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
