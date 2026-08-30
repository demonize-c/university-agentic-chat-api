import asyncio
import logging
from ..db.session import engine, Base
from ..models import Document  # Ensure models are imported for Base metadata registration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created / verified successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(init_db())
