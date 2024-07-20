import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.environ["DATABASE_URL"]
    uploads_path: str = os.environ["UPLOADS_PATH"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
