from functools import lru_cache
from os import getenv

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None


load_dotenv()


class Settings(BaseModel):
    model_provider: str = Field(default=getenv("MODEL_PROVIDER", "mock"))
    openai_api_key: str = Field(default=getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default=getenv("OPENAI_MODEL", "gpt-4.1-mini"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
