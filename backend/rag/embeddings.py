"""
Embedding generation using sentence-transformers.
Uses all-MiniLM-L6-v2 for fast, lightweight embeddings (384 dimensions).
"""
import numpy as np

_model = None


def _get_model():
    """Lazy-load the embedding model"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded: all-MiniLM-L6-v2")
    return _model


def generate_embeddings(texts: list) -> np.ndarray:
    """Generate embeddings for a list of texts"""
    model = _get_model()
    return model.encode(texts, show_progress_bar=True, convert_to_numpy=True)


def generate_single_embedding(text: str) -> np.ndarray:
    """Generate embedding for a single query"""
    model = _get_model()
    return model.encode([text], convert_to_numpy=True)[0]
