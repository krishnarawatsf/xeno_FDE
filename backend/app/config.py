from pydantic_settings import BaseSettings


def _normalize_service_url(url: str) -> str:
    """Ensure service URLs include a scheme (Render env vars may be host-only)."""
    if url and not url.startswith(("http://", "https://")):
        return f"https://{url.rstrip('/')}"
    return url.rstrip("/")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./xeno_crm.db"
    redis_url: str = "redis://localhost:6379/0"
    channel_service_url: str = "http://localhost:8001"
    crm_callback_url: str = "http://localhost:8000"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"

    @property
    def normalized_channel_service_url(self) -> str:
        return _normalize_service_url(self.channel_service_url)

    @property
    def normalized_crm_callback_url(self) -> str:
        return _normalize_service_url(self.crm_callback_url)


settings = Settings()
