"""
Tax service — Product-specific GST/VAT rates by country.
India: Real HSN-based GST slabs per product category.
International: Standard VAT/Sales Tax rates.
"""

# ── India GST by product category (HSN-based) ───────────────────────────
INDIA_GST = {
    # Industrial machinery & equipment — 18%
    "Industrial Control Valves":      18.0,
    "Hydraulic Pressure Sensors":     18.0,
    "Pneumatic Actuators":            18.0,
    "Temperature Control Units":      18.0,
    "Flow Meters":                    18.0,
    "Servo Motor Drive Units":        18.0,
    "Industrial Pumps":               18.0,
    # Solar / renewable — 12%
    "Solar Panel Modules":            12.0,
    "Solar Inverters":                12.0,
    # Generic fallback
    "_default":                       18.0,
}

# ── Country rules ────────────────────────────────────────────────────────
TAX_RULES = {
    "India":     {"name": "GST",               "rate": 18.0,  "symbol": "₹",  "currency": "INR"},
    "USA":       {"name": "Sales Tax",         "rate": 8.5,   "symbol": "$",  "currency": "USD"},
    "UK":        {"name": "VAT",               "rate": 20.0,  "symbol": "£",  "currency": "GBP"},
    "UAE":       {"name": "VAT",               "rate": 5.0,   "symbol": "AED ", "currency": "AED"},
    "Germany":   {"name": "VAT",               "rate": 19.0,  "symbol": "€",  "currency": "EUR"},
    "France":    {"name": "TVA",               "rate": 20.0,  "symbol": "€",  "currency": "EUR"},
    "Singapore": {"name": "GST",               "rate": 9.0,   "symbol": "S$", "currency": "SGD"},
    "Japan":     {"name": "Consumption Tax",   "rate": 10.0,  "symbol": "¥",  "currency": "JPY"},
    "Canada":    {"name": "GST+HST",           "rate": 13.0,  "symbol": "C$", "currency": "CAD"},
    "Australia": {"name": "GST",               "rate": 10.0,  "symbol": "A$", "currency": "AUD"},
    "China":     {"name": "VAT",               "rate": 13.0,  "symbol": "¥",  "currency": "CNY"},
    "Brazil":    {"name": "ICMS+IPI",          "rate": 22.0,  "symbol": "R$", "currency": "BRL"},
    "Mexico":    {"name": "IVA",               "rate": 16.0,  "symbol": "$",  "currency": "MXN"},
    "South Africa": {"name": "VAT",            "rate": 15.0,  "symbol": "R",  "currency": "ZAR"},
    "Netherlands": {"name": "BTW/VAT",         "rate": 21.0,  "symbol": "€",  "currency": "EUR"},
    "Italy":     {"name": "IVA",               "rate": 22.0,  "symbol": "€",  "currency": "EUR"},
}


def get_india_gst_rate(product: str) -> float:
    """Look up India GST rate for a specific product."""
    for key, rate in INDIA_GST.items():
        if key.lower() in (product or "").lower() or (product or "").lower() in key.lower():
            return rate
    return INDIA_GST["_default"]


def calculate_tax(amount: float, country: str = "India", product: str = None) -> dict:
    """Calculate applicable tax based on country and product."""
    rule = TAX_RULES.get(country, TAX_RULES["India"])

    # Product-specific rate for India
    if country == "India" and product:
        rate = get_india_gst_rate(product)
    else:
        rate = rule["rate"]

    tax_amount = round(amount * rate / 100, 2)

    return {
        "subtotal":   round(amount, 2),
        "tax_name":   rule["name"],
        "tax_rate":   rate,
        "tax_amount": tax_amount,
        "total":      round(amount + tax_amount, 2),
        "country":    country,
        "currency":   rule["currency"],
        "symbol":     rule["symbol"],
    }


def get_available_regions() -> list:
    """List all supported tax regions with currency info."""
    return [
        {
            "country":   k,
            "tax_name":  v["name"],
            "rate":      v["rate"],
            "currency":  v["currency"],
            "symbol":    v["symbol"],
        }
        for k, v in TAX_RULES.items()
    ]
