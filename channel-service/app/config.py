from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    crm_callback_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
