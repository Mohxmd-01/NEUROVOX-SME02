"""
Agent 3: Competitor Analysis — Queries market intelligence database.
Returns competitor pricing landscape for strategic decision-making.
"""
import json
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import CompetitorData


def _load_competitor_db():
    """Load competitor intelligence database"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "competitor_db.json")
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_competitor_analysis(product: str) -> CompetitorData:
    """Analyze competitor pricing landscape for a product"""
    
    db = _load_competitor_db()
    
    # Find matching product
    matched = None
    product_lower = product.lower().replace("-", " ").replace("_", " ")
    
    for item in db["market_data"]:
        item_lower = item["product"].lower()
        if product_lower in item_lower or item_lower in product_lower:
            matched = item
            break
        # Word overlap
        overlap = set(product_lower.split()) & set(item_lower.split())
        if len(overlap) >= 1:
            matched = item
    
    if not matched:
        matched = db["market_data"][0]
    
    # Add slight market variance to simulate real-time data
    variance = random.uniform(-3, 3)
    
    return CompetitorData(
        product=matched["product"],
        competitor_name=matched["top_competitor"],
        competitor_price=round(matched["competitor_price"] + variance, 2),
        market_avg=matched["market_avg"],
        market_low=matched["market_low"],
        market_high=matched["market_high"],
        competitors=matched.get("competitors", {})
    )
