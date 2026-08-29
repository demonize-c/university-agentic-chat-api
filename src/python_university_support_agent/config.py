from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR: Path = BASE_DIR / "storage"

class Settings(BaseSettings):
    database_host: str
    database_port: int = 3306
    database_user: str
    database_password: str
    database_name: str

    redis_host: str
    redis_port: str

    
    hf_token: str


    storage_dir: Path = STORAGE_DIR

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()