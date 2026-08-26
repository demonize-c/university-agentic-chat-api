from fastapi import FastAPI
from .routers import docs_router
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from .config import settings
from .logger import get_logger


app_logger = get_logger("APP")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis = await create_pool(RedisSettings(
            host = settings.redis_host,
            port = int(settings.redis_port)
        ))
        await app.state.redis.ping()
        app_logger.info(f"Redis connected on host: {settings.redis_host} | port: {settings.redis_port}")
        yield
    except Exception:
        app_logger.exception(
            "Redis connection failed | host=%s | port=%s",
            settings.redis_host,
            settings.redis_port,
        )
        raise

    finally:
        if app.state.redis:
            await app.state.redis.close()

            app_logger.info(
                "Redis connection closed"
            )



app = FastAPI(lifespan=lifespan)
app.include_router( docs_router )






# import os
# from dotenv import load_dotenv
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# import pypdf;
# from langchain_core.documents import Document;
# from .retrieval import get_vector_store, get_embeddings


# load_dotenv()

# # HF_TOKEN = os.getenv('HF_TOKEN');
# # print(HF_TOKEN)

# # file_path = ".//data//nke-10k-2023.pdf";
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.join(BASE_DIR, "data", "nke-10k-2023.pdf")
# reader = pypdf.PdfReader(file_path);

# docs = list();

# for i, page in enumerate(reader.pages):
#     page_content = page.extract_text()
#     docs.append(Document(page_content=page_content or "", metadata = { "source": file_path, "page": i}))

# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,      # max characters per chunk
#     chunk_overlap=200,    # overlap between chunks (preserves context across boundaries)
#     add_start_index=True  # track index of chunk in original document
# )

# all_splits = text_splitter.split_documents(docs)



# embeddings = get_embeddings();

# vector_store = get_vector_store( embeddings )

# vector_store.add_documents(all_splits)

    
    

