import asyncio
from sqlalchemy import text
from python_university_support_agent.db import engine, Base, AsyncSessionLocal
from python_university_support_agent.logger import get_logger

logger = get_logger("Reset DB Script")


async def reset_db_data():
    logger.info("Deleting all document and job records from database...")
    try:
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(text("DELETE FROM embedding_jobs"))
                await db.execute(text("DELETE FROM documents"))
                await db.commit()
                logger.info("Database records cleared successfully.")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error clearing database records: {e}")
                raise e
    finally:
        await engine.dispose()


async def reset_db_tables():
    logger.info("Dropping and re-creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables recreated successfully.")
    except Exception as e:
        logger.error(f"Error recreating database tables: {e}")
        raise e
    finally:
        await engine.dispose()



def main():
    asyncio.run(reset_db_data())


if __name__ == "__main__":
    main()

