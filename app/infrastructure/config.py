from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    reserva_ttl_segundos: int = 600

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()