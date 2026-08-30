from ..retrieval import get_vector_store, get_embeddings


embeddings = get_embeddings();

vector_store = get_vector_store( embeddings )

results = vector_store.similarity_search(
    query="How accurately does Shakespeare portray the historical Henry V and the Battle of Agincourt?",
    k=4  # top-k results
)

for doc in results:
    print(doc.page_content, doc.metadata)