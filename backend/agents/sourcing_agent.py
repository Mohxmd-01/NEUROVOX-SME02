"""
Global Sourcing Engine — Agent for IntelliQuote Platform
=========================================================
Generates Local / Export-Offshore / Near-Client sourcing options for any product,
scores them using a weighted multi-criteria framework, and returns the optimal
sourcing decision alongside two alternatives.

Weighting model:
  Cost efficiency   35 %
  Logistics cost    20 %
  Delivery speed    20 %
  Quality score     15 %
  Tax/duty burden   10 %
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import SupplierOption, SourcingDecision

# ── Supplier database ───────────────────────────────────────────────────────
# Each entry: country → {cost_index, logistics_index, quality, lead_days, duty_rate}
# cost_index  : multiplier vs baseline India cost (1.0 = same, 0.7 = 30% cheaper)
# logistics_index: INR per unit (flat estimate)
# quality     : 0.0–1.0
# lead_days   : typical delivery days FROM that source TO client
# duty_rate   : import duty % applicable when shipping internationally

SUPPLIER_DB = {
    "India": {
        "cost_index": 1.0,
        "logistics_per_unit": 80,     # domestic freight
        "quality": 0.80,
        "lead_days": 7,
        "duty_rate": 0.0,             # no import duty domestic
        "region": "South Asia",
    },
    "China": {
        "cost_index": 0.62,
        "logistics_per_unit": 320,    # sea freight per unit equiv
        "quality": 0.72,
        "lead_days": 28,
        "duty_rate": 12.5,
        "region": "East Asia",
    },
    "Vietnam": {
        "cost_index": 0.68,
        "logistics_per_unit": 290,
        "quality": 0.74,
        "lead_days": 24,
        "duty_rate": 10.0,
        "region": "Southeast Asia",
    },
    "Germany": {
        "cost_index": 1.45,
        "logistics_per_unit": 480,
        "quality": 0.96,
        "lead_days": 18,
        "duty_rate": 8.0,
        "region": "Western Europe",
    },
    "USA": {
        "cost_index": 1.38,
        "logistics_per_unit": 520,
        "quality": 0.94,
        "lead_days": 22,
        "duty_rate": 7.5,
        "region": "North America",
    },
    "UAE": {
        "cost_index": 1.10,
        "logistics_per_unit": 180,
        "quality": 0.83,
        "lead_days": 10,
        "duty_rate": 5.0,
        "region": "Middle East",
    },
    "Singapore": {
        "cost_index": 1.22,
        "logistics_per_unit": 240,
        "quality": 0.90,
        "lead_days": 14,
        "duty_rate": 4.0,
        "region": "Southeast Asia",
    },
    "Bangladesh": {
        "cost_index": 0.58,
        "logistics_per_unit": 180,
        "quality": 0.65,
        "lead_days": 18,
        "duty_rate": 8.0,
        "region": "South Asia",
    },
    "Mexico": {
        "cost_index": 0.78,
        "logistics_per_unit": 350,
        "quality": 0.78,
        "lead_days": 20,
        "duty_rate": 6.0,
        "region": "Latin America",
    },
}

# ── Near-client mapping (best logistics hub near each client country) ──────
NEAR_CLIENT_MAP = {
    "USA":     "Mexico",
    "UK":      "Germany",
    "Germany": "Germany",
    "France":  "Germany",
    "UAE":     "UAE",
    "Japan":   "Singapore",
    "Singapore": "Singapore",
    "Canada":  "USA",
    "India":   "India",       # domestic is near-client for India
    "Australia": "Singapore",
}

# ── Weights ────────────────────────────────────────────────────────────────
WEIGHTS = {
    "cost":      0.35,
    "logistics": 0.20,
    "delivery":  0.20,
    "quality":   0.15,
    "tax":       0.10,
}


def _compute_landed_cost(baseline_cost: float, supplier: dict) -> dict:
    """Calculate all cost components from a supplier entry"""
    cost_pu      = round(baseline_cost * supplier["cost_index"], 2)
    logistics_pu = supplier["logistics_per_unit"]
    duty_rate    = supplier["duty_rate"]
    tax_amount   = round((cost_pu + logistics_pu) * duty_rate / 100, 2)
    total        = round(cost_pu + logistics_pu + tax_amount, 2)
    return {
        "cost_per_unit":     cost_pu,
        "logistics_cost":    logistics_pu,
        "tax_rate":          duty_rate,
        "tax_amount":        tax_amount,
        "total_landed_cost": total,
        "delivery_days":     supplier["lead_days"],
        "quality_score":     supplier["quality"],
    }


def _score_option(data: dict, all_costs: list, all_logistics: list,
                  all_delivery: list, all_taxes: list) -> float:
    """
    Compute a normalized 0–100 weighted score.
    For cost/logistics/delivery/tax: lower is better (invert).
    For quality: higher is better.
    """
    def norm_inv(val, lo, hi):
        if hi == lo:
            return 100.0
        return round((1 - (val - lo) / (hi - lo)) * 100, 1)

    def norm_fwd(val, lo, hi):
        if hi == lo:
            return 100.0
        return round(((val - lo) / (hi - lo)) * 100, 1)

    c_min, c_max = min(all_costs),    max(all_costs)
    l_min, l_max = min(all_logistics), max(all_logistics)
    d_min, d_max = min(all_delivery), max(all_delivery)
    t_min, t_max = min(all_taxes),   max(all_taxes)

    s_cost      = norm_inv(data["total_landed_cost"], c_min, c_max)
    s_logistics = norm_inv(data["logistics_cost"],    l_min, l_max)
    s_delivery  = norm_inv(data["delivery_days"],     d_min, d_max)
    s_quality   = norm_fwd(data["quality_score"],     0.60,  1.00) * 100 / 100
    s_tax       = norm_inv(data["tax_rate"],          t_min, t_max)

    weighted = (
        s_cost      * WEIGHTS["cost"]      +
        s_logistics * WEIGHTS["logistics"] +
        s_delivery  * WEIGHTS["delivery"]  +
        s_quality   * WEIGHTS["quality"]   +
        s_tax       * WEIGHTS["tax"]
    )
    return round(weighted, 1)


def _build_supplier_option(
    option_type: str,
    country: str,
    baseline_cost: float,
    scored: float,
    data: dict,
) -> SupplierOption:
    """Construct a SupplierOption model from raw data"""
    supplier = SUPPLIER_DB[country]
    type_labels = {
        "local":      f"Local ({country})",
        "export":     f"Offshore ({country})",
        "near_client": f"Near-Client ({country})",
    }
    reasonings = {
        "local": (
            f"Domestic supply from {country} — fastest delivery ({data['delivery_days']} days), "
            f"zero import duty, strong logistics network. Quality: {int(data['quality_score']*100)}%."
        ),
        "export": (
            f"Offshore sourcing from {country} — lowest unit cost "
            f"(₹{data['cost_per_unit']:,.0f}/unit, {int((1-SUPPLIER_DB[country]['cost_index'])*100)}% cheaper), "
            f"but longer lead time ({data['delivery_days']} days) and {data['tax_rate']}% import duty."
        ),
        "near_client": (
            f"Near-client supply from {country} — reduces last-mile logistics cost, "
            f"delivery in {data['delivery_days']} days, {data['tax_rate']}% duty. "
            f"Quality: {int(data['quality_score']*100)}%. Balances speed and cost."
        ),
    }
    return SupplierOption(
        option_type=option_type,
        country=country,
        region_label=type_labels[option_type],
        cost_per_unit=data["cost_per_unit"],
        logistics_cost=data["logistics_cost"],
        tax_rate=data["tax_rate"],
        tax_amount=data["tax_amount"],
        total_landed_cost=data["total_landed_cost"],
        delivery_days=data["delivery_days"],
        quality_score=data["quality_score"],
        weighted_score=scored,
        reasoning=reasonings[option_type],
    )


def get_sourcing_options(
    product: str,
    client_country: str,
    quantity: int,
    baseline_cost_per_unit: float,
) -> SourcingDecision:
    """
    Main entry point: produce Local / Export / Near-Client options and return
    the optimal SourcingDecision.

    Args:
        product: product name (for context)
        client_country: client's country (determines near-client hub)
        quantity: order quantity (affects logistics scaling)
        baseline_cost_per_unit: current internal cost (INR) used as reference
    """
    # ── Select three candidates ────────────────────────────────────────────
    local_country      = "India"
    export_country     = "China"   # cheapest offshore by default
    near_client_country = NEAR_CLIENT_MAP.get(client_country, "UAE")

    # Avoid duplicate options
    if near_client_country == local_country:
        near_client_country = "UAE"
    if export_country == near_client_country:
        export_country = "Vietnam"

    candidates = {
        "local":       local_country,
        "export":      export_country,
        "near_client": near_client_country,
    }

    # ── Compute landed costs for each ─────────────────────────────────────
    raw = {}
    for otype, country in candidates.items():
        supplier = SUPPLIER_DB.get(country, SUPPLIER_DB["India"])
        raw[otype] = _compute_landed_cost(baseline_cost_per_unit, supplier)

    # ── Collect normalization arrays ───────────────────────────────────────
    all_costs     = [d["total_landed_cost"] for d in raw.values()]
    all_logistics = [d["logistics_cost"]    for d in raw.values()]
    all_delivery  = [d["delivery_days"]     for d in raw.values()]
    all_taxes     = [d["tax_rate"]          for d in raw.values()]

    # ── Score each option ─────────────────────────────────────────────────
    scored = {
        otype: _score_option(data, all_costs, all_logistics, all_delivery, all_taxes)
        for otype, data in raw.items()
    }

    # ── Build SupplierOption objects ──────────────────────────────────────
    options: dict[str, SupplierOption] = {}
    for otype, country in candidates.items():
        options[otype] = _build_supplier_option(
            otype, country, baseline_cost_per_unit, scored[otype], raw[otype]
        )

    # ── Select winner ─────────────────────────────────────────────────────
    best_type = max(scored, key=scored.get)
    recommended = options[best_type]
    alternatives = [o for t, o in options.items() if t != best_type]

    # ── Cost impact vs baseline ───────────────────────────────────────────
    savings_per_unit  = round(baseline_cost_per_unit - recommended.total_landed_cost, 2)
    cost_impact_pct   = round((savings_per_unit / baseline_cost_per_unit) * 100, 1) if baseline_cost_per_unit else 0
    delivery_baseline = SUPPLIER_DB["India"]["lead_days"]
    delivery_impact   = recommended.delivery_days - delivery_baseline

    # ── Strategy note ─────────────────────────────────────────────────────
    if savings_per_unit > 0:
        strategy_note = (
            f"Sourcing from {recommended.country} saves ₹{savings_per_unit:,.2f}/unit "
            f"({abs(cost_impact_pct)}% cost reduction). "
            f"This margin improvement allows more competitive pricing or higher profit retention."
        )
    elif savings_per_unit < 0:
        strategy_note = (
            f"Sourcing from {recommended.country} costs ₹{abs(savings_per_unit):,.2f}/unit more "
            f"than domestic ({abs(cost_impact_pct)}% premium) but offers superior quality "
            f"({int(recommended.quality_score*100)}%) and speed ({recommended.delivery_days} days). "
            f"This supports a premium pricing strategy."
        )
    else:
        strategy_note = (
            f"Sourcing from {recommended.country} is cost-neutral but improves "
            f"delivery speed to {recommended.delivery_days} days."
        )

    sourcing_reasoning = (
        f"Evaluated {len(options)} sourcing options: "
        + ", ".join(
            f"{t.replace('_',' ')} from {o.country} (score {scored[t]:.0f}/100)"
            for t, o in options.items()
        )
        + f". Optimal: {recommended.region_label} with weighted score {recommended.weighted_score:.0f}/100."
    )

    return SourcingDecision(
        recommended=recommended,
        alternatives=alternatives,
        sourcing_reasoning=sourcing_reasoning,
        cost_impact_percent=cost_impact_pct,
        delivery_impact_days=delivery_impact,
        savings_per_unit=savings_per_unit,
        strategy_note=strategy_note,
    )
