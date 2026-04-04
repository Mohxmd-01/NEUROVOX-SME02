"""
Currency conversion service — live rates via exchangerate-api.com (free tier).
Falls back to well-calibrated static rates if network is unavailable.
"""
import requests

# ── Static fallback rates (INR base, updated Apr 2026) ──────────────────
_STATIC_RATES = {
    "INR": 1.0,
    "USD": 83.5,
    "EUR": 90.2,
    "GBP": 105.8,
    "AED": 22.7,
    "JPY": 0.558,
    "SGD": 62.1,
    "CAD": 61.5,
    "AUD": 54.3,
    "CNY": 11.5,
    "BRL": 16.5,
    "MXN": 4.85,
    "ZAR": 4.6,
}

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AED": "AED ",
    "JPY": "¥",
    "SGD": "S$",
    "CAD": "C$",
    "AUD": "A$",
    "CNY": "¥",
    "BRL": "R$",
    "MXN": "MX$",
    "ZAR": "R",
}

COUNTRY_CURRENCY = {
    "India":        "INR",
    "USA":          "USD",
    "UK":           "GBP",
    "UAE":          "AED",
    "Germany":      "EUR",
    "France":       "EUR",
    "Singapore":    "SGD",
    "Japan":        "JPY",
    "Canada":       "CAD",
    "Australia":    "AUD",
    "China":        "CNY",
    "Brazil":       "BRL",
    "Mexico":       "MXN",
    "South Africa": "ZAR",
    "Netherlands":  "EUR",
    "Italy":        "EUR",
}

_live_rates_cache: dict = {}


def _fetch_live_rates() -> dict:
    """Attempt to fetch live rates from open.er-api.com (free, no key needed)."""
    global _live_rates_cache
    if _live_rates_cache:
        return _live_rates_cache
    try:
        resp = requests.get(
            "https://open.er-api.com/v6/latest/INR",
            timeout=3,
        )
        if resp.status_code == 200:
            data = resp.json()
            # rates are in "how much of target per 1 INR" — we want INR per target
            raw = data.get("rates", {})
            # Convert: rate = 1/raw[X] gives "INR per 1 X"
            rates = {k: round(1.0 / v, 6) for k, v in raw.items() if v > 0}
            rates["INR"] = 1.0
            _live_rates_cache = rates
            return rates
    except Exception:
        pass
    return {}


def convert_currency(amount_inr: float, target_currency: str) -> dict:
    """Convert INR amount to target currency using live or static rates."""
    target = target_currency.upper()

    # Try live rates first
    live = _fetch_live_rates()
    rate = live.get(target) or _STATIC_RATES.get(target, 1.0)

    converted = round(amount_inr / rate, 2)

    return {
        "original_inr": round(amount_inr, 2),
        "converted":    converted,
        "currency":     target,
        "symbol":       CURRENCY_SYMBOLS.get(target, target + " "),
        "rate":         rate,
        "source":       "live" if target in live else "static",
    }


def convert_for_country(amount_inr: float, country: str) -> dict:
    """Convert INR to the local currency of a given country."""
    currency = COUNTRY_CURRENCY.get(country, "USD")
    result = convert_currency(amount_inr, currency)
    return result


def get_symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency.upper(), currency)
