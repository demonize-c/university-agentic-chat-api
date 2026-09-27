from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR: Path = BASE_DIR / "storage"

class Settings(BaseSettings):
    database_host: str = "localhost"
    database_port: int = 3306
    database_user: str = "root"
    database_password: str = ""
    database_name: str = "university_agent"

    redis_host: str = "localhost"
    redis_port: str = "6379"

    hf_token: str = ""

    base_dir: Path = BASE_DIR
    storage_dir: Path = STORAGE_DIR

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )



settings = Settings()