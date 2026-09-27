import asyncio
from pathlib import Path
from python_university_support_agent.scripts.clear_vector_store import clear_vector_store
from python_university_support_agent.scripts.reset_db import reset_db_data
from python_university_support_agent.db import engine
from python_university_support_agent.config import settings
from python_university_support_agent.logger import get_logger

logger = get_logger("Reset All Script")


def clear_storage_files():
    logger.info("Cleaning up storage directory files...")
    storage_docs_dir = settings.storage_dir.joinpath("documents")
    if storage_docs_dir.exists():
        for file_path in storage_docs_dir.glob("*"):
            if file_path.name != ".gitkeep" and file_path.is_file():
                file_path.unlink()
    logger.info("Storage directory files cleaned up successfully.")


async def reset_all():
    logger.info("Starting complete cleanup (Vector Store, DB Data, Storage Files)...")
    clear_vector_store()
    await reset_db_data()
    clear_storage_files()
    await engine.dispose()
    logger.info("All data, vector embeddings, and storage files reset successfully!")



def main():
    asyncio.run(reset_all())


if __name__ == "__main__":
    main()

