"""
Agent 4: Knowledge Agent — SME01 integration.
Retrieves relevant company knowledge with conflict detection.
This is the bridge between the RAG engine and the strategy agent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.retriever import search_knowledge
from rag.conflict_detector import detect_conflicts
from models import KnowledgeContext
from typing import List


def get_knowledge_context(query: str, product: str = "", client: str = "") -> List[KnowledgeContext]:
    """
    SME01 Integration: Retrieve relevant company knowledge.
    Searches across all ingested documents (PDFs, Excel, Emails).
    Detects and resolves conflicts between sources.
    """
    
    # Build enriched search query
    enriched_query = query
    if product:
        enriched_query += f" product: {product}"
    if client:
        enriched_query += f" client: {client}"
    
    # Search across all documents
    raw_results = search_knowledge(enriched_query, top_k=5)
    
    if not raw_results:
        return []
    
    # Check for conflicts among results
    conflicts = detect_conflicts(raw_results)
    
    # Build KnowledgeContext objects
    contexts = []
    for result in raw_results:
        chunk_id = result.get("id", "")
        conflict_info = conflicts.get(chunk_id, None)
        
        ctx = KnowledgeContext(
            relevant_text=result.get("text", ""),
            source_document=result.get("source", "unknown"),
            source_section=result.get("section", "unknown"),
            confidence=result.get("score", 0.0),
            conflict_detected=conflict_info is not None,
            conflict_details=conflict_info["details"] if conflict_info else None,
            chosen_source=conflict_info["chosen"] if conflict_info else None,
            conflict_reason=conflict_info["reason"] if conflict_info else None
        )
        contexts.append(ctx)
    
    return contexts
