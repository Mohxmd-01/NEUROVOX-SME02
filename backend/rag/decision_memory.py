"""
RAG Decision Memory — SME02 Upgrade
Stores past quote decisions as searchable embeddings. Acts as "experience memory"
for the strategy engine — similar past cases are retrieved and passed to the LLM.

Keeps a SEPARATE FAISS index from company documents to avoid contamination.
"""
import os
import json
import numpy as np

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index", "decisions")
MEMORY_INDEX_PATH = os.path.join(MEMORY_DIR, "decisions.bin")
MEMORY_META_PATH = os.path.join(MEMORY_DIR, "decisions_meta.json")

_memory_index = None
_memory_meta: list = []


def _get_model():
    """Lazy-load the same embedding model used by the main RAG"""
    from rag.embeddings import generate_single_embedding, generate_embeddings
    return generate_single_embedding, generate_embeddings


def _load_memory() -> bool:
    """Load decision memory index from disk"""
    global _memory_index, _memory_meta
    try:
        import faiss
        if os.path.exists(MEMORY_INDEX_PATH) and os.path.exists(MEMORY_META_PATH):
            _memory_index = faiss.read_index(MEMORY_INDEX_PATH)
            with open(MEMORY_META_PATH, "r", encoding="utf-8") as f:
                _memory_meta = json.load(f)
            print(f"✅ Decision memory loaded: {len(_memory_meta)} past cases")
            return True
    except Exception as e:
        print(f"⚠️ Could not load decision memory: {e}")
    return False


def _save_memory():
    """Persist decision memory index to disk"""
    global _memory_index, _memory_meta
    import faiss
    os.makedirs(MEMORY_DIR, exist_ok=True)
    faiss.write_index(_memory_index, MEMORY_INDEX_PATH)
    with open(MEMORY_META_PATH, "w", encoding="utf-8") as f:
        json.dump(_memory_meta, f, indent=2, ensure_ascii=False)


def save_decision(quote_id: str, product: str, quantity: int, strategy_type: str,
                  final_price: float, margin_percent: float, win_probability: str,
                  client_country: str, reasoning: str):
    """
    Save a completed quote decision into memory.
    Called by main.py after every successful RFP processing.
    """
    global _memory_index, _memory_meta

    import faiss
    from rag.embeddings import generate_single_embedding

    # Build a searchable text representation of this decision
    summary_text = (
        f"Product: {product}. Quantity: {quantity} units. "
        f"Strategy: {strategy_type}. Final price: {final_price}. "
        f"Margin: {margin_percent}%. Win probability: {win_probability}. "
        f"Country: {client_country}. Reasoning: {reasoning[:300]}"
    )

    embedding = generate_single_embedding(summary_text).astype("float32").reshape(1, -1)
    dim = embedding.shape[1]

    if _memory_index is None:
        _load_memory()

    if _memory_index is None or _memory_index.d != dim:
        _memory_index = faiss.IndexFlatL2(dim)
        _memory_meta = []

    _memory_index.add(embedding)
    _memory_meta.append({
        "quote_id": quote_id,
        "product": product,
        "quantity": quantity,
        "strategy_type": strategy_type,
        "final_price": final_price,
        "margin_percent": margin_percent,
        "win_probability": win_probability,
        "client_country": client_country,
        "reasoning_summary": reasoning[:400],
        "text": summary_text,
    })

    _save_memory()
    print(f"✅ Decision memory saved: {quote_id} → {len(_memory_meta)} total cases")


def recall_similar_cases(product: str, quantity: int, top_k: int = 3) -> list:
    """
    Retrieve the most similar past decisions for a given product+quantity query.
    Returns a list of memory records sorted by similarity.
    """
    global _memory_index, _memory_meta

    if _memory_index is None:
        _load_memory()

    if _memory_index is None or _memory_index.ntotal == 0:
        return []

    from rag.embeddings import generate_single_embedding

    query = f"Product: {product}. Quantity: {quantity} units."
    embedding = generate_single_embedding(query).astype("float32").reshape(1, -1)

    k = min(top_k, _memory_index.ntotal)
    distances, indices = _memory_index.search(embedding, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if 0 <= idx < len(_memory_meta):
            entry = _memory_meta[idx].copy()
            entry["similarity"] = round(float(1 / (1 + distances[0][i])), 3)
            results.append(entry)

    return results


def get_memory_stats() -> dict:
    """Return stats about stored decision memory"""
    global _memory_index, _memory_meta
    if _memory_index is None:
        _load_memory()
    return {
        "total_cases": len(_memory_meta),
        "index_loaded": _memory_index is not None,
        "strategies_used": list(set(m.get("strategy_type", "") for m in _memory_meta)),
    }
