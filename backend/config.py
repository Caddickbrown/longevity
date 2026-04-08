from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    garmin_email: str = ""
    garmin_password: str = ""
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./longevity.db"
    health_at_home_url: str = "http://localhost:49999"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
