from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ..config import settings


DATABASE_URL = (
    f"mysql+pymysql://"
    f"{settings.database_user}:{settings.database_password}"
    f"@{settings.database_host}:{settings.database_port}"
    f"/{settings.database_name}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
sessionLocal = SessionLocal  # backward compatibility alias
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

