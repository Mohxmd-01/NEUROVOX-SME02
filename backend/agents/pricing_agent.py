"""
Agent 2: Pricing Agent — Queries the internal pricing database.
Applies bulk discount tiers and checks stock availability.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import PricingData


def _load_pricing_db():
    """Load the internal pricing database"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing_db.json")
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fuzzy_match(query: str, products: list) -> dict:
    """Find best matching product by name"""
    query_lower = query.lower().replace("-", " ").replace("_", " ")
    
    best_match = None
    best_score = 0
    
    for item in products:
        name_lower = item["name"].lower()
        
        # Exact substring match
        if query_lower in name_lower or name_lower in query_lower:
            return item
        
        # Word overlap scoring
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        overlap = len(query_words & name_words)
        
        if overlap > best_score:
            best_score = overlap
            best_match = item
    
    # If no good match, return first product as default
    return best_match if best_match and best_score > 0 else products[0]


def get_pricing(product: str, quantity: int) -> PricingData:
    """Get pricing data for a product with bulk discount calculation"""
    
    db = _load_pricing_db()
    matched = _fuzzy_match(product, db["products"])
    
    # Calculate applicable bulk discount
    bulk_discount = 0
    for tier in matched.get("bulk_tiers", []):
        if quantity >= tier["min_qty"]:
            bulk_discount = tier["discount_percent"]
    
    return PricingData(
        product=matched["name"],
        cost_per_unit=matched["cost_per_unit"],
        base_price=matched.get("base_price", matched["cost_per_unit"] * 1.3),
        min_margin_percent=matched["min_margin_percent"],
        bulk_discount_percent=bulk_discount,
        available_stock=matched["available_stock"]
    )


def list_all_products() -> list:
    """List all products in the catalog"""
    db = _load_pricing_db()
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "base_price": p.get("base_price", p["cost_per_unit"] * 1.3),
            "available_stock": p["available_stock"]
        }
        for p in db["products"]
    ]
