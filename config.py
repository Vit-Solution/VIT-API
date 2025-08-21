from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env_name: str = "Local Environment"
    base_url: str = "http://localhost:8000"
    secret_key: str = ""
    algorithm: str = ""
    mongodb_connection_string: str = ""
    redis_host: str = ""
    redis_port: int = ""
    redis_password: str = ""

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")
    print(f"BASE_URL: ", settings.base_url)
    return settings

# print("ENV_NAME: ", get_settings().env_name)
# print("BASE_URL: ", get_settings().base_url)
# print("DATABASE_URL: ", get_settings().database_url)