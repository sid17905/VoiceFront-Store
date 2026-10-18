"""
packages/common_utils/multicurrency.py

Global multi-currency and localization support for Phase 3 scaling.
Handles currency conversion rates, symbol formatting, and regional localization settings.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CurrencyConfig:
    code: str
    symbol: str
    rate_to_inr: float

SUPPORTED_CURRENCIES = {
    "INR": CurrencyConfig("INR", "₹", 1.0),
    "USD": CurrencyConfig("$", "$", 83.0),
    "EUR": CurrencyConfig("EUR", "€", 90.0),
    "GBP": CurrencyConfig("GBP", "£", 105.0),
}

def convert_and_format_price(amount: float, target_currency: str = "INR") -> str:
    config = SUPPORTED_CURRENCIES.get(target_currency, SUPPORTED_CURRENCIES["INR"])
    converted_amount = amount / config.rate_to_inr
    return f"{config.symbol}{converted_amount:,.2f}"
