from typing import Dict

CATEGORY_KEYWORDS = {
    "groceries": ["milk", "bread", "eggs", "cheese", "butter", "yogurt"],
    "snacks": ["chips", "cookie", "cracker", "chocolate", "crisps", "snack"],
    "beverages": ["water", "soda", "coke", "pepsi", "juice", "coffee", "tea"],
    "produce": ["apple", "banana", "orange", "tomato", "potato", "lettuce"],
    "meat": ["chicken", "beef", "pork", "sausage", "steak"],
    "bakery": ["bread", "bun", "bagel", "pastry", "croissant"],
    "pharmacy": ["tab", "tablet", "capsule", "mg", "ml", "oral", "syrup", "solution", "tabnet", "rx", "drug", "pill"],
    "delivery": ["delivery", "home delivery", "shipping", "service", "charge"],
}


def categorize_item(name: str) -> str:
    n = name.lower()
    # direct keyword match
    for cat, keys in CATEGORY_KEYWORDS.items():
        for k in keys:
            if k in n:
                return cat
    # fallback heuristics
    if any(ch.isdigit() for ch in n) and ("mg" in n or "ml" in n):
        return "pharmacy"
    if "delivery" in n or "home" in n and "charge" in n:
        return "delivery"
    return "other"


def categorize_items(items: list) -> list:
    for it in items:
        it["category"] = categorize_item(it.get("name", ""))
    return items
