"""
Feedback Service — Records quote outcome (won/lost) for continuous learning.
Outcomes are stored in a lightweight JSON file and fed back into decision memory.
"""
import os
import json
from datetime import datetime
from typing import Optional

FEEDBACK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "feedback_outcomes.json")


def _load_feedback() -> list:
    """Load existing feedback records"""
    try:
        if os.path.exists(FEEDBACK_PATH):
            with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_feedback(records: list):
    """Persist feedback to disk"""
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def record_feedback(
    quote_id: str,
    outcome: str,  # "won" | "lost" | "pending"
    actual_price: Optional[float] = None,
    client_feedback: Optional[str] = None,
    quote_data: Optional[dict] = None,  # full quote context for memory enrichment
) -> dict:
    """
    Record the real-world outcome of a quote decision.
    Also updates decision memory with outcome info for future learning.
    """
    records = _load_feedback()

    # Check for existing entry (update if exists)
    existing_idx = next((i for i, r in enumerate(records) if r.get("quote_id") == quote_id), None)

    entry = {
        "quote_id": quote_id,
        "outcome": outcome,
        "actual_price": actual_price,
        "client_feedback": client_feedback,
        "recorded_at": datetime.now().isoformat(),
        "quote_data": quote_data or {},
    }

    if existing_idx is not None:
        records[existing_idx] = entry
    else:
        records.append(entry)

    _save_feedback(records)

    # Enrich decision memory with outcome
    if quote_data:
        try:
            _enrich_memory_with_outcome(quote_id, outcome, actual_price, quote_data)
        except Exception as e:
            print(f"⚠️ Memory enrichment skipped: {e}")

    print(f"✅ Feedback recorded: {quote_id} → {outcome}")
    return entry


def _enrich_memory_with_outcome(
    quote_id: str, outcome: str, actual_price: Optional[float], quote_data: dict
):
    """Update decision memory to include outcome info for better future decisions"""
    from rag.decision_memory import save_decision

    strategy = quote_data.get("strategy", {})
    parsed = quote_data.get("parsed_rfp", {})
    pricing = quote_data.get("pricing", {})

    outcome_label = f"OUTCOME={outcome.upper()}"
    if actual_price:
        outcome_label += f" actual_price={actual_price}"

    save_decision(
        quote_id=f"{quote_id}_outcome",
        product=pricing.get("product", strategy.get("geo_region", "Unknown")),
        quantity=parsed.get("quantity", 0),
        strategy_type=strategy.get("strategy_type", "balanced"),
        final_price=actual_price or strategy.get("final_price", 0),
        margin_percent=strategy.get("margin_percent", 0),
        win_probability=f"{outcome}:{strategy.get('win_probability', 'N/A')}",
        client_country=parsed.get("client_country", "India"),
        reasoning=f"{outcome_label}. Original: {strategy.get('reasoning', '')[:300]}",
    )


def get_feedback_stats() -> dict:
    """Get win/loss statistics from feedback records"""
    records = _load_feedback()

    total = len(records)
    won = sum(1 for r in records if r.get("outcome") == "won")
    lost = sum(1 for r in records if r.get("outcome") == "lost")
    pending = total - won - lost

    win_rate = round((won / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_feedback": total,
        "won": won,
        "lost": lost,
        "pending": pending,
        "win_rate": win_rate,
        "records": records[-10:],  # last 10
    }


def get_quote_feedback(quote_id: str) -> Optional[dict]:
    """Get feedback for a specific quote"""
    records = _load_feedback()
    return next((r for r in records if r.get("quote_id") == quote_id), None)
