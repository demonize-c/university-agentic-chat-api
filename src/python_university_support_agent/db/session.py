from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ..config import settings


DATABASE_URL = (
    f"mysql+pymysql://"
    f"{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}"
    f"/{settings.db_name}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
sessionLocal = sessionmaker( bind=engine, autoflush=False, autocommit=False)
Base = declarative_base();

def get_db():
    db = sessionLocal()
    try:
        yield db
    except:
        db.close()

      
