from datetime import timedelta
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env_name: str = "Local Environment"
    base_url: str = "http://localhost:8000"
    secret_key: str = ""
    algorithm: str = ""
    access_token_expire_minutes: int = 300
    mongodb_connection_string: str = ""
    redis_host: str = ""
    redis_port: int = 6379
    redis_password: str = ""
    rag_api_url: str = ""

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")
    print(f"BASE_URL: ", settings.base_url)
    return settings


# --------------------------------------------- mongo connection string ---------------------------------------------
mongodb_connection_string: str = get_settings().mongodb_connection_string

# --------------------------------------------- redis connection ---------------------------------------------
REDIS_HOST = get_settings().redis_host
REDIS_PORT = get_settings().redis_port
REDIS_PASSWORD = get_settings().redis_password
REDIS_EXPIRE = timedelta(minutes=5)  # Cache expiration time

# --------------------------------------------- jwt connection ---------------------------------------------
SECRET_KEY = get_settings().secret_key
ALGORITHM = get_settings().algorithm
ACCESS_TOKEN_EXPIRE = get_settings().access_token_expire_minutes

# --------------------------------------------- rag api connection ---------------------------------------------
RAG_API_URL = get_settings().rag_api_url