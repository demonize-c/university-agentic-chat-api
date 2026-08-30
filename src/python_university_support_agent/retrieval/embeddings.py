import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings



load_dotenv()

def get_embeddings():
    embeddings = HuggingFaceEndpointEmbeddings(
        model ="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token = os.getenv('HF_TOKEN'),
        task = "feature-extraction"
    )
    return embeddings