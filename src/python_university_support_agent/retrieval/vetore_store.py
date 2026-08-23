from langchain_chroma import Chroma

def get_vector_store( embeddings ):
     vector_store = Chroma(
        collection_name   = "university_docs",
        persist_directory = "./croma_db",
        embedding_function=embeddings
     )
     return vector_store