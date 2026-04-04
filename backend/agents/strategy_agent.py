"""
Agent 5: Strategy Decision Engine — SME02 UPGRADED VERSION (Production)

Changes from v2:
- Added negotiation_tactics to LLM output schema
- Added win_probability_pct (numeric) for comparison table
- Added compute_strategy_variant() helper for multi-strategy comparison endpoint
- Unified single LLM call with ALL context (pricing + competitor + knowledge + memory + geo)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.llm_service import call_llm
from models import PricingData, CompetitorData, KnowledgeContext, StrategyDecision, StrategyVariant, SourcingDecision
from typing import List, Optional


# --- Geo mapping helpers ---
COUNTRY_TO_CURRENCY = {
    "USA": "USD", "UK": "GBP", "UAE": "AED", "Germany": "EUR",
    "Japan": "JPY", "Singapore": "SGD", "Canada": "CAD", "India": "INR",
    "France": "EUR", "Australia": "AUD",
}

DOMESTIC_COUNTRIES = {"India"}


def _parse_win_pct(win_str: str) -> float:
    """Extract numeric win probability from string like '70-80%' or '75%'"""
    try:
        import re
        nums = re.findall(r'\d+', str(win_str))
        if len(nums) >= 2:
            return round((float(nums[0]) + float(nums[1])) / 2, 1)
        elif len(nums) == 1:
            return float(nums[0])
    except Exception:
        pass
    return 60.0


def decide_strategy(
    pricing: PricingData,
    competitor: CompetitorData,
    knowledge: List[KnowledgeContext],
    quantity: int,
    special_requirements: List[str] = [],
    strategy_mode: str = "balanced",
    client_country: str = "India",
    tax_info: dict = None,
    currency_info: dict = None,
    sourcing: Optional[SourcingDecision] = None,
) -> StrategyDecision:
    """
    SME02 Unified Strategy Engine — Production Edition.

    Flow:
    1. Compute hard financial constraints (rules)
    2. Detect below-cost pivot trigger (Twist 2)
    3. Detect geo context (Twist 1)
    4. Recall similar past decisions from memory
    5. Single unified LLM call with ALL context
    6. Enforce price floor on LLM output
    7. Return enriched StrategyDecision with negotiation tactics
    """

    cost = pricing.cost_per_unit
    base_price = pricing.base_price
    min_margin = pricing.min_margin_percent
    bulk_discount = pricing.bulk_discount_percent
    comp_price = competitor.competitor_price
    market_avg = competitor.market_avg
    market_low = competitor.market_low
    market_high = competitor.market_high

    # ── Apply sourcing cost adjustment ──
    sourcing_context_text = "No global sourcing data available."
    if sourcing:
        # Use recommended sourcing landed cost if it improves our position
        if sourcing.savings_per_unit > 0:
            cost = min(cost, sourcing.recommended.total_landed_cost)
        sourcing_context_text = (
            f"Global Sourcing Engine: Optimal source = {sourcing.recommended.region_label} "
            f"(score {sourcing.recommended.weighted_score:.0f}/100). "
            f"Landed cost: ₹{sourcing.recommended.total_landed_cost:,.0f}/unit. "
            f"Savings vs baseline: ₹{sourcing.savings_per_unit:,.0f}/unit ({sourcing.cost_impact_percent:.1f}% impact). "
            f"Delivery: {sourcing.recommended.delivery_days} days. "
            f"Quality score: {int(sourcing.recommended.quality_score*100)}%. "
            f"Strategy note: {sourcing.strategy_note}"
        )

    # ── Step 1: Hard financial constraints ──
    min_price = cost * (1 + min_margin / 100)
    discounted_base = base_price * (1 - bulk_discount / 100)

    # ── Step 2: TWIST 2 — Below-cost pivot detection ──
    below_cost_pivot = comp_price < cost
    if below_cost_pivot:
        rule_strategy = "value-based"
        rule_price = min_price * 1.05
        rule_risk = "medium"
        rule_win = "45-55%"
        forced_value_additions = [
            "Extended 2-year warranty (vs industry standard 1 year)",
            "Premium 24/7 technical support",
            "Free expedited delivery within 7 days",
            "Free installation and commissioning",
        ]
    elif strategy_mode == "aggressive":
        if comp_price > min_price:
            rule_strategy = "aggressive"
            rule_price = max(min_price, comp_price * 0.93)
            rule_risk = "medium"
            rule_win = "75-85%"
            forced_value_additions = []
        else:
            rule_strategy = "value-based"
            rule_price = min_price * 1.02
            rule_risk = "high"
            rule_win = "50-60%"
            forced_value_additions = ["Free installation", "Extended warranty", "Priority support"]
    elif strategy_mode == "premium":
        rule_strategy = "premium"
        rule_price = max(discounted_base, market_avg * 1.02)
        rule_risk = "medium"
        rule_win = "40-55%"
        forced_value_additions = [
            "2-year extended warranty", "Dedicated account manager",
            "Free training sessions", "Priority support SLA"
        ]
    else:  # balanced
        if comp_price > (cost * 1.25):
            rule_strategy = "competitive"
            rule_price = comp_price * 0.95
            rule_risk = "low"
            rule_win = "70-80%"
            forced_value_additions = []
        elif comp_price > min_price:
            rule_strategy = "balanced"
            rule_price = (min_price + comp_price) / 2
            rule_risk = "low"
            rule_win = "55-65%"
            forced_value_additions = []
        else:
            rule_strategy = "premium"
            rule_price = min_price * 1.08
            rule_risk = "high"
            rule_win = "35-45%"
            forced_value_additions = ["Extended warranty", "Dedicated account manager"]

    # ── Step 3: TWIST 1 — Geo-aware context ──
    is_international = client_country not in DOMESTIC_COUNTRIES
    geo_currency = COUNTRY_TO_CURRENCY.get(client_country, "INR")

    geo_context = ""
    if not is_international:
        geo_context = (
            f"CLIENT IS DOMESTIC (India). Prioritize: faster delivery timelines, "
            f"local sourcing advantages, GST-compliant pricing. "
            f"Emphasize speed and reliability as differentiators."
        )
    else:
        geo_context = (
            f"CLIENT IS INTERNATIONAL ({client_country}). Consider: "
            f"currency conversion to {geo_currency}, import duty implications, "
            f"longer lead times, and international payment terms. "
        )
        if tax_info:
            geo_context += f"Applicable tax: {tax_info.get('tax_name','N/A')} at {tax_info.get('tax_rate','N/A')}%. "
        if currency_info:
            geo_context += (
                f"Converted total: {currency_info.get('symbol','')}"
                f"{currency_info.get('converted','N/A')} {geo_currency}."
            )

    # ── Step 4: Recall similar past decisions ──
    past_cases = []
    past_cases_text = "No prior decisions in memory yet."
    try:
        from rag.decision_memory import recall_similar_cases
        past_cases = recall_similar_cases(pricing.product, quantity, top_k=3)
        if past_cases:
            past_cases_text = "\n".join([
                f"  Past Case {i+1}: {c['strategy_type']} strategy, "
                f"₹{c['final_price']}/unit, margin {c['margin_percent']}%, "
                f"win prob {c['win_probability']}, country: {c['client_country']} "
                f"(similarity: {c['similarity']})"
                for i, c in enumerate(past_cases)
            ])
    except Exception as e:
        print(f"⚠️ Memory recall skipped: {e}")

    # ── Step 5: Knowledge context summary ──
    knowledge_text = "\n".join([
        f"  [{k.source_document} / {k.source_section}]: {k.relevant_text[:200]}"
        for k in knowledge if k.confidence > 0.3
    ]) or "No relevant knowledge found."

    conflict_text = "\n".join([
        f"  CONFLICT: {k.conflict_details} → Resolved: {k.chosen_source} ({k.conflict_reason})"
        for k in knowledge if k.conflict_detected
    ]) or "None."

    # ── Step 6: UNIFIED LLM CALL ──
    system_prompt = """You are an elite B2B sales strategist and pricing expert for TechFlow Industries.
You have access to full market intelligence, internal cost data, competitor landscape,
company knowledge, and historical deal memory.

Your job is to produce a rich, well-reasoned pricing decision in JSON format.

CRITICAL RULES:
- NEVER recommend a final_price below the minimum_viable_price provided
- Your reasoning must cite specific data points (costs, competitor prices, margins)
- insights must be actionable bullet points (3-5 items)
- confidence_score: 0.0-1.0 based on data quality and certainty of outcome
- Be specific, not generic. Reference actual numbers.
- negotiation_tactics: 2-3 specific tactics with concrete numbers (e.g., "If client negotiates below ₹X, offer free installation instead of reducing price")
- win_probability: express as a range like "70-80%"

Return ONLY valid JSON in this exact structure:
{
  "reasoning": "3-5 sentence professional rationale with specific data references",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "confidence_score": 0.85,
  "win_probability": "70-80%",
  "risk_level": "low",
  "value_additions": ["addition 1", "addition 2"],
  "negotiation_tactics": [
    "If client requests price reduction, offer extended warranty instead of lowering price by more than 3%",
    "If budget is ₹X, propose phased delivery to spread cost",
    "Emphasize ISO certification and local support as differentiators vs cheaper competitors"
  ]
}
"""

    user_prompt = f"""
=== RFP CONTEXT ===
Product: {pricing.product}
Quantity: {quantity} units
Client Country: {client_country}
Special Requirements: {', '.join(special_requirements) if special_requirements else 'None'}
Strategy Mode Requested: {strategy_mode}

=== FINANCIAL DATA ===
Our Cost per Unit: ₹{cost}
Base List Price: ₹{base_price}
Bulk Discount Applied: {bulk_discount}%
Minimum Required Margin: {min_margin}%
Minimum Viable Price (FLOOR): ₹{min_price:.2f}
Rule-Based Recommended Price: ₹{rule_price:.2f}
Rule-Based Strategy: {rule_strategy}

=== COMPETITOR LANDSCAPE ===
Top Competitor: {competitor.competitor_name} @ ₹{comp_price}/unit
Market Average: ₹{market_avg}
Market Range: ₹{market_low} – ₹{market_high}
BELOW-COST PIVOT TRIGGERED: {below_cost_pivot}
(Competitor price ₹{comp_price} {'IS' if below_cost_pivot else 'is NOT'} below our cost ₹{cost})

=== GLOBAL SOURCING INTELLIGENCE ===
{sourcing_context_text}

=== GEO-INTELLIGENCE ===
{geo_context}

=== COMPANY KNOWLEDGE BASE ===
{knowledge_text}

Conflicts: {conflict_text}

=== DECISION MEMORY (Similar Past Cases) ===
{past_cases_text}

=== YOUR TASK ===
Given all the above, provide:
1. A professional reasoning narrative (cite actual numbers)
2. 3-5 actionable insights the sales team should know
3. Your confidence in this decision (0.0-1.0)
4. Realistic win probability range (e.g., "70-80%")
5. Risk level (low/medium/high)
6. Value additions to offer (especially if below-cost pivot is triggered)
7. 2-3 specific negotiation tactics with actual numbers/thresholds

Remember: final_price must be >= ₹{min_price:.2f}
"""

    llm_result = _call_unified_llm(system_prompt, user_prompt)

    # ── Step 7: Merge results — rules set price, LLM enriches reasoning ──
    final_price = max(rule_price, min_price)  # Hard floor enforced

    reasoning = llm_result.get("reasoning", _fallback_reasoning(rule_strategy, rule_price, comp_price, cost))
    insights = llm_result.get("insights", _fallback_insights(rule_strategy, below_cost_pivot, is_international))
    confidence_score = float(llm_result.get("confidence_score", 0.6))
    confidence_score = max(0.0, min(1.0, confidence_score))
    win_probability = llm_result.get("win_probability", rule_win)
    risk_level = llm_result.get("risk_level", rule_risk)
    negotiation_tactics = llm_result.get("negotiation_tactics", _fallback_negotiation(rule_strategy, comp_price, cost))

    # Value additions: merge forced (from rules) + LLM suggestions
    llm_value_adds = llm_result.get("value_additions", [])
    all_value_adds = forced_value_additions[:]
    for va in llm_value_adds:
        if va not in all_value_adds:
            all_value_adds.append(va)

    # Final margin calculation
    margin_percent = round(((final_price - cost) / cost) * 100, 2)

    # Alternative scenarios
    alternatives = {
        "aggressive": round(max(min_price, comp_price * 0.92), 2),
        "balanced": round(max(min_price, (min_price + comp_price) / 2), 2),
        "premium": round(max(discounted_base, market_avg * 1.05), 2),
    }

    return StrategyDecision(
        final_price=round(final_price, 2),
        strategy_type=rule_strategy,
        reasoning=reasoning,
        margin_percent=margin_percent,
        risk_level=risk_level,
        value_additions=all_value_adds,
        alternative_prices=alternatives,
        win_probability=win_probability,
        insights=insights,
        confidence_score=round(confidence_score, 2),
        geo_region=client_country,
        geo_currency=geo_currency,
        past_cases_used=len(past_cases),
        below_cost_pivot=below_cost_pivot,
        negotiation_tactics=negotiation_tactics,
        win_probability_pct=_parse_win_pct(win_probability),
    )


def compute_strategy_variant(
    pricing: PricingData,
    competitor: CompetitorData,
    knowledge: List[KnowledgeContext],
    quantity: int,
    strategy_mode: str,
    client_country: str = "India",
    tax_info: dict = None,
    currency_info: dict = None,
) -> StrategyVariant:
    """
    Compute a single strategy variant (for multi-strategy comparison endpoint).
    Uses a lightweight rule-only path — no LLM call for speed.
    """
    cost = pricing.cost_per_unit
    base_price = pricing.base_price
    min_margin = pricing.min_margin_percent
    bulk_discount = pricing.bulk_discount_percent
    comp_price = competitor.competitor_price
    market_avg = competitor.market_avg

    min_price = cost * (1 + min_margin / 100)
    discounted_base = base_price * (1 - bulk_discount / 100)
    below_cost = comp_price < cost

    if below_cost:
        strategy_type = "value-based"
        price = min_price * 1.05
        risk = "medium"
        win_str = "45-55%"
        win_pct = 50.0
        value_adds = [
            "Extended 2-year warranty",
            "Free expedited delivery",
            "Free installation & commissioning",
        ]
        reasoning = (
            f"Competitor price ₹{comp_price} falls below our cost ₹{cost}. "
            f"Value-based strategy at ₹{price:.0f} emphasizes service and reliability differentiators."
        )
    elif strategy_mode == "aggressive":
        price = max(min_price, comp_price * 0.93)
        strategy_type = "aggressive"
        risk = "medium"
        win_str = "75-85%"
        win_pct = 80.0
        value_adds = []
        reasoning = (
            f"Aggressive pricing at ₹{price:.0f} (7% below competitor ₹{comp_price}) "
            f"maximizes win probability. Margin: {round(((price-cost)/cost)*100,1)}%."
        )
    elif strategy_mode == "premium":
        price = max(discounted_base, market_avg * 1.05)
        strategy_type = "premium"
        risk = "medium"
        win_str = "40-55%"
        win_pct = 47.5
        value_adds = [
            "2-year extended warranty",
            "Dedicated account manager",
            "Free training sessions",
        ]
        reasoning = (
            f"Premium positioning at ₹{price:.0f} (above market avg ₹{market_avg}) "
            f"protects margins at {round(((price-cost)/cost)*100,1)}% while emphasizing quality."
        )
    else:  # balanced
        price = max(min_price, (min_price + comp_price) / 2)
        strategy_type = "balanced"
        risk = "low"
        win_str = "60-70%"
        win_pct = 65.0
        value_adds = []
        reasoning = (
            f"Balanced pricing at ₹{price:.0f} — midpoint between cost floor ₹{min_price:.0f} "
            f"and competitor ₹{comp_price}. Healthy {round(((price-cost)/cost)*100,1)}% margin."
        )

    price = max(price, min_price)  # Hard floor
    margin = round(((price - cost) / cost) * 100, 2)

    return StrategyVariant(
        strategy_type=strategy_type,
        final_price=round(price, 2),
        margin_percent=margin,
        win_probability=win_str,
        win_probability_pct=win_pct,
        risk_level=risk,
        reasoning=reasoning,
        value_additions=value_adds,
    )


def _call_unified_llm(system_prompt: str, user_prompt: str) -> dict:
    """Single unified LLM call with robust fallback"""
    try:
        result = call_llm(system_prompt, user_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception as e:
        print(f"⚠️ Unified LLM call failed: {e}")
    return {}


def _fallback_reasoning(strategy: str, price: float, comp_price: float, cost: float) -> str:
    """Safe fallback if LLM is unavailable"""
    return (
        f"Rule-based {strategy} strategy applied. "
        f"Recommended price ₹{price:.2f} based on our cost of ₹{cost} "
        f"and competitor benchmark of ₹{comp_price}. "
        f"This maintains required margins while positioning competitively."
    )


def _fallback_insights(strategy: str, below_cost: bool, international: bool) -> list:
    """Safe fallback insights if LLM is unavailable"""
    insights = [f"Strategy selected: {strategy} based on market conditions."]
    if below_cost:
        insights.append("Competitor is pricing below our cost — value differentiation is essential.")
    if international:
        insights.append("International client — factor in currency risk and longer delivery lead times.")
    insights.append("Review alternative price points before finalising the proposal.")
    return insights


def _fallback_negotiation(strategy: str, comp_price: float, cost: float) -> list:
    """Safe fallback negotiation tactics if LLM is unavailable"""
    floor = cost * 1.12
    return [
        f"If client requests lower price, offer free installation (worth ₹{round(cost*0.05):,}) instead of reducing unit price.",
        f"If client compares to competitor at ₹{comp_price:,.0f}, highlight ISO certification, local support, and warranty advantages.",
        f"Minimum acceptable price is ₹{floor:,.0f}/unit — below this, propose phased delivery or smaller initial order.",
    ]
