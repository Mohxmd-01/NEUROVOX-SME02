"""
Semantic search retriever — high-level interface for knowledge queries.
"""
from rag.embeddings import generate_single_embedding
from rag.vector_store import search


def search_knowledge(query: str, top_k: int = 5) -> list:
    """
    Main retrieval function.
    Takes a natural language query and returns relevant document chunks.
    """
    embedding = generate_single_embedding(query)
    results = search(embedding, top_k)
    return results
