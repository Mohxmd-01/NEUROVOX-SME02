from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class ParsedRFP(BaseModel):
    product: str
    quantity: int
    deadline: str
    budget_hint: Optional[str] = None
    special_requirements: List[str] = []
    client_name: Optional[str] = None
    client_country: Optional[str] = "India"
    raw_text: str


class PricingData(BaseModel):
    product: str
    cost_per_unit: float
    base_price: float
    min_margin_percent: float
    bulk_discount_percent: float
    available_stock: int


class CompetitorData(BaseModel):
    product: str
    competitor_name: str
    competitor_price: float
    market_avg: float
    market_low: float
    market_high: float
    competitors: Optional[Dict] = {}


class KnowledgeContext(BaseModel):
    relevant_text: str
    source_document: str
    source_section: str
    confidence: float
    conflict_detected: bool = False
    conflict_details: Optional[str] = None
    chosen_source: Optional[str] = None
    conflict_reason: Optional[str] = None


# ─── Global Sourcing Models ───────────────────────────────────────────────────

class SupplierOption(BaseModel):
    """A single sourcing option from a specific country/region"""
    option_type: str          # "local" | "export" | "near_client"
    country: str
    region_label: str         # e.g. "Local (India)", "Offshore (China)", "Near-Client (Germany)"
    cost_per_unit: float      # manufacturing / purchase cost in INR
    logistics_cost: float     # per-unit freight/shipping cost in INR
    tax_rate: float           # import duty / GST % applicable
    tax_amount: float         # tax per unit in INR
    total_landed_cost: float  # cost + logistics + tax
    delivery_days: int        # estimated delivery time
    quality_score: float      # 0.0–1.0
    weighted_score: float     # final weighted score 0–100
    reasoning: str            # short explanation


class SourcingDecision(BaseModel):
    """Output from the Global Sourcing Engine"""
    recommended: SupplierOption
    alternatives: List[SupplierOption] = []
    sourcing_reasoning: str
    cost_impact_percent: float    # % cost change vs baseline internal cost
    delivery_impact_days: int     # days vs baseline
    savings_per_unit: float       # INR saved vs baseline
    strategy_note: str            # how sourcing affects pricing strategy

# ─────────────────────────────────────────────────────────────────────────────


class StrategyDecision(BaseModel):
    final_price: float
    strategy_type: str
    reasoning: str
    margin_percent: float
    risk_level: str
    value_additions: List[str] = []
    alternative_prices: dict = {}
    win_probability: Optional[str] = None
    # --- SME02 Upgrades ---
    insights: List[str] = []              # LLM bullet-point insights
    confidence_score: float = 0.0         # 0.0-1.0 decision confidence
    geo_region: Optional[str] = None      # Geo-aware region label
    geo_currency: Optional[str] = None    # Target currency code
    past_cases_used: int = 0              # How many memory cases influenced decision
    below_cost_pivot: bool = False        # Twist 2: was value-pivot triggered?
    # --- Production Upgrade ---
    negotiation_tactics: List[str] = []   # AI negotiation recommendations
    win_probability_pct: Optional[float] = None  # Numeric win prob for comparison


class StrategyVariant(BaseModel):
    """Single strategy variant for comparison table"""
    strategy_type: str
    final_price: float
    margin_percent: float
    win_probability: str
    win_probability_pct: float
    risk_level: str
    reasoning: str
    value_additions: List[str] = []


class StrategiesComparison(BaseModel):
    """All strategy variants for comparison"""
    aggressive: StrategyVariant
    balanced: StrategyVariant
    premium: StrategyVariant
    recommended: str  # which one is recommended


class FeedbackEntry(BaseModel):
    """Outcome feedback for a quote decision"""
    quote_id: str
    outcome: str             # "won" | "lost" | "pending"
    actual_price: Optional[float] = None
    client_feedback: Optional[str] = None
    recorded_at: str = ""


class DecisionMemoryEntry(BaseModel):
    """Lightweight record stored in decision memory index (Twist 2 - experience memory)"""
    quote_id: str
    product: str
    quantity: int
    strategy_type: str
    final_price: float
    margin_percent: float
    win_probability: str
    client_country: str
    reasoning_summary: str


class QuoteOutput(BaseModel):
    id: str
    created_at: str
    client_name: str
    parsed_rfp: ParsedRFP
    pricing: PricingData
    competitor: CompetitorData
    knowledge_context: List[KnowledgeContext]
    strategy: StrategyDecision
    sourcing: Optional[SourcingDecision] = None  # Global Sourcing Engine result
    pdf_path: Optional[str] = None
    status: str = "draft"
    outcome: Optional[str] = None  # "won" | "lost" | "pending"
