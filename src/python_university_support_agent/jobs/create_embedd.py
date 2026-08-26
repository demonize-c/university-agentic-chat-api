


async def create_embedd(ctx, doc_id):
    from ..logger import get_logger
    logger = get_logger(f" Doc<{doc_id}> | Embedd Task")
    logger.info("Task started")
