"""
Conflict detection module — uses LLM to find contradictions across documents.
When multiple sources say different things, this identifies and resolves the conflict.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.llm_service import call_llm
from typing import List, Dict


CONFLICT_SYSTEM_PROMPT = """You are a data consistency analyst for a business knowledge system.

Given multiple text snippets from different company documents, identify if any contain 
contradictory information (different prices, different policies, different terms, different margins).

Return JSON:
{
    "conflicts_found": true or false,
    "conflicts": [
        {
            "snippet_indices": [0, 2],
            "description": "what contradicts between these snippets",
            "recommended_source_index": 0,
            "reason": "why this source is more reliable (newer date, official policy doc, etc.)"
        }
    ]
}

Rules for choosing which source to trust:
1. Newer date wins over older date
2. Official policy documents win over emails
3. CFO/Manager communications win over general staff emails
4. Excel pricing sheets are the source of truth for prices
5. If dates are the same, prefer the more specific document
"""


def detect_conflicts(results: List[Dict]) -> Dict:
    """
    Analyze retrieved documents for contradictions.
    Returns a dict mapping chunk IDs to conflict information.
    """
    if len(results) < 2:
        return {}
    
    texts = [r.get("text", "")[:400] for r in results]
    sources = [r.get("source", "unknown") for r in results]
    dates = [r.get("date", "unknown") for r in results]
    
    user_prompt = "Analyze these document snippets for contradictions:\n\n"
    for i, (text, source, date) in enumerate(zip(texts, sources, dates)):
        user_prompt += f"[Snippet {i}] Source: {source} | Date: {date}\n{text}\n\n"
    
    try:
        result = call_llm(CONFLICT_SYSTEM_PROMPT, user_prompt, json_mode=True)
        
        if isinstance(result, dict) and result.get("conflicts_found"):
            conflicts = {}
            for conflict in result.get("conflicts", []):
                indices = conflict.get("snippet_indices", [])
                rec_idx = conflict.get("recommended_source_index", 0)
                
                for idx in indices:
                    if idx < len(results):
                        chunk_id = results[idx].get("id", f"chunk_{idx}")
                        conflicts[chunk_id] = {
                            "details": conflict.get("description", "Conflict detected"),
                            "chosen": sources[rec_idx] if rec_idx < len(sources) else sources[0],
                            "reason": conflict.get("reason", "Most recent/authoritative source")
                        }
            return conflicts
    except Exception as e:
        print(f"⚠️ Conflict detection failed: {e}")
    
    return {}
