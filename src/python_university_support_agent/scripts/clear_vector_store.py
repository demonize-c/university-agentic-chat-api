from python_university_support_agent.retrieval import get_vector_store, get_embeddings
from python_university_support_agent.logger import get_logger

logger = get_logger("Clear Vector Store Script")


def clear_vector_store():
    logger.info("Clearing all vector embeddings from ChromaDB...")
    try:
        embeddings = get_embeddings()
        vector_store = get_vector_store(embeddings)
        collection = vector_store._collection
        count_before = collection.count()
        logger.info(f"Vector embeddings count before deletion: {count_before}")

        if count_before > 0:
            existing_items = collection.get()
            if existing_items and existing_items.get("ids"):
                collection.delete(ids=existing_items["ids"])

        count_after = collection.count()
        logger.info(f"Vector embeddings cleared successfully! Count after deletion: {count_after}")
    except Exception as e:
        logger.error(f"Error clearing vector store: {e}")
        raise e


if __name__ == "__main__":
    clear_vector_store()
