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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
