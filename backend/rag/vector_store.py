"""
FAISS vector store — build, save, load, and search operations.
"""
import faiss
import numpy as np
import json
import os

INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index")
INDEX_PATH = os.path.join(INDEX_DIR, "index.bin")
METADATA_PATH = os.path.join(INDEX_DIR, "metadata.json")

_index = None
_metadata = []


def build_index(embeddings: np.ndarray, chunks: list):
    """Build FAISS index from embeddings and save to disk"""
    global _index, _metadata
    
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    dimension = embeddings.shape[1]
    _index = faiss.IndexFlatL2(dimension)
    _index.add(embeddings.astype('float32'))
    _metadata = chunks
    
    # Save to disk
    faiss.write_index(_index, INDEX_PATH)
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ FAISS index built: {len(chunks)} vectors, {dimension}D")


def load_index() -> bool:
    """Load existing FAISS index from disk"""
    global _index, _metadata
    
    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        _index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            _metadata = json.load(f)
        print(f"✅ FAISS index loaded: {len(_metadata)} chunks")
        return True
    
    print("⚠️ No existing FAISS index found")
    return False


def search(query_embedding: np.ndarray, top_k: int = 5) -> list:
    """Search FAISS index for nearest neighbors"""
    global _index, _metadata
    
    if _index is None:
        if not load_index():
            return []
    
    if _index.ntotal == 0:
        return []
    
    query_vec = query_embedding.reshape(1, -1).astype('float32')
    k = min(top_k, _index.ntotal)
    distances, indices = _index.search(query_vec, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(_metadata):
            result = _metadata[idx].copy()
            # Convert L2 distance to similarity score (0-1)
            result["score"] = float(1 / (1 + distances[0][i]))
            results.append(result)
    
    return results


def get_index_stats() -> dict:
    """Get statistics about the current index"""
    global _index, _metadata
    
    if _index is None:
        load_index()
    
    return {
        "total_vectors": _index.ntotal if _index else 0,
        "total_chunks": len(_metadata),
        "sources": list(set(m.get("source", "unknown") for m in _metadata)),
        "index_loaded": _index is not None
    }
