from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    crm_callback_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
