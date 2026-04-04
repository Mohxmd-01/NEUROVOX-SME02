"""
Agent 1: RFP Parser — Extracts structured requirements from unstructured RFP text.
Uses LLM to intelligently parse product, quantity, deadline, budget, and special requirements.
"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.llm_service import call_llm
from models import ParsedRFP


# ── City / keyword → country mapping for robust detection ────────────────
LOCATION_COUNTRY_MAP = {
    # India
    "mumbai": "India", "delhi": "India", "bangalore": "India",
    "bengaluru": "India", "chennai": "India", "hyderabad": "India",
    "pune": "India", "kolkata": "India", "ahmedabad": "India",
    "surat": "India", "jaipur": "India", "lucknow": "India",
    "india": "India", "भारत": "India",
    # USA
    "usa": "USA", "united states": "USA", "u.s.a": "USA",
    "texas": "USA", "houston": "USA", "new york": "USA",
    "california": "USA", "chicago": "USA", "los angeles": "USA",
    "seattle": "USA", "boston": "USA", "miami": "USA",
    "dallas": "USA", "atlanta": "USA", "denver": "USA",
    # UK
    "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
    "london": "UK", "manchester": "UK", "birmingham": "UK",
    # UAE
    "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE", "sharjah": "UAE",
    "united arab emirates": "UAE",
    # Germany
    "germany": "Germany", "berlin": "Germany", "munich": "Germany",
    "hamburg": "Germany", "frankfurt": "Germany", "stuttgart": "Germany",
    # France
    "france": "France", "paris": "France", "lyon": "France",
    # Singapore
    "singapore": "Singapore",
    # Japan
    "japan": "Japan", "tokyo": "Japan", "osaka": "Japan",
    # Canada
    "canada": "Canada", "toronto": "Canada", "vancouver": "Canada",
    "montreal": "Canada",
    # Australia
    "australia": "Australia", "sydney": "Australia", "melbourne": "Australia",
    # China
    "china": "China", "beijing": "China", "shanghai": "China",
    "shenzhen": "China", "guangzhou": "China",
    # Brazil
    "brazil": "Brazil", "são paulo": "Brazil", "sao paulo": "Brazil",
    "rio de janeiro": "Brazil",
    # Mexico
    "mexico": "Mexico", "mexico city": "Mexico",
    # South Africa
    "south africa": "South Africa", "johannesburg": "South Africa",
    "cape town": "South Africa",
    # Netherlands
    "netherlands": "Netherlands", "amsterdam": "Netherlands",
    # Italy
    "italy": "Italy", "rome": "Italy", "milan": "Italy",
}

# Currency symbol → country hints
CURRENCY_COUNTRY_HINTS = {
    "₹": "India", "inr": "India",
    "usd": "USA", "dollar": "USA",
    "gbp": "UK", "£": "UK",
    "aed": "UAE",
    "eur": "Germany", "€": "Germany",
    "sgd": "Singapore",
    "jpy": "Japan", "¥": "Japan",
    "cad": "Canada",
    "aud": "Australia",
    "cny": "China",
    "brl": "Brazil",
    "mxn": "Mexico",
    "zar": "South Africa",
}


def _detect_country_from_text(text: str) -> str | None:
    """Heuristic country detection from raw text via location/currency keywords."""
    lower = text.lower()
    # 1. Check location names
    for keyword, country in LOCATION_COUNTRY_MAP.items():
        if keyword in lower:
            return country
    # 2. Check currency mentions
    for keyword, country in CURRENCY_COUNTRY_HINTS.items():
        if keyword in lower:
            return country
    return None


PARSER_SYSTEM_PROMPT = """You are an expert RFP analyst for a manufacturing SME called TechFlow Industries.
Extract structured information from the RFP text.

Return JSON with these exact fields:
{
    "product": "product name or category (match to: Industrial Control Valves, Hydraulic Pressure Sensors, Pneumatic Actuators, Temperature Control Units, Flow Meters, Servo Motor Drive Units, Industrial Pumps, Solar Panel Modules, Solar Inverters, Flow Meters)",
    "quantity": integer number of units,
    "deadline": "delivery deadline as stated",
    "budget_hint": "any budget/price mentioned or null",
    "special_requirements": ["list of special conditions"],
    "client_name": "company/client name or null",
    "client_country": "infer from cities, states, country names, currency symbols in the text. Examples: Mumbai/Delhi/Chennai → India, Texas/Houston/New York → USA, London → UK, Dubai → UAE, Berlin/Munich → Germany, Paris → France, Tokyo → Japan, Singapore → Singapore. Default to India if unclear."
}

Rules:
- If quantity is a range, use the higher number
- Always extract quantity as an integer
- Match product names as closely as possible to our catalog
- Detect currency: ₹ = India, $ = USA, £ = UK, € = Europe, AED = UAE
- client_country MUST be one of: India, USA, UK, UAE, Germany, France, Singapore, Japan, Canada, Australia, China, Brazil, Mexico, South Africa, Netherlands, Italy
"""


def parse_rfp(rfp_text: str) -> ParsedRFP:
    """Parse unstructured RFP text into structured data"""

    result = call_llm(PARSER_SYSTEM_PROMPT, f"Parse this RFP:\n\n{rfp_text}")

    if isinstance(result, dict) and "error" not in result:
        # If LLM returned "India" as default but text suggests otherwise, use heuristic
        llm_country = result.get("client_country", "India")
        if llm_country == "India":
            heuristic = _detect_country_from_text(rfp_text)
            if heuristic:
                llm_country = heuristic

        return ParsedRFP(
            product=result.get("product", "Unknown Product"),
            quantity=int(result.get("quantity", 0)),
            deadline=result.get("deadline", "Not specified"),
            budget_hint=result.get("budget_hint"),
            special_requirements=result.get("special_requirements", []),
            client_name=result.get("client_name"),
            client_country=llm_country,
            raw_text=rfp_text
        )

    # Fallback: heuristic-only extraction
    detected_country = _detect_country_from_text(rfp_text) or "India"
    return ParsedRFP(
        product="Unknown Product",
        quantity=0,
        deadline="Not specified",
        budget_hint=None,
        special_requirements=[],
        client_name=None,
        client_country=detected_country,
        raw_text=rfp_text
    )

