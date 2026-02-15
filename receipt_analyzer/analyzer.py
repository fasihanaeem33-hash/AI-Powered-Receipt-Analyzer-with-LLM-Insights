from collections import defaultdict
from typing import Dict, List


def analyze_items(items: List[Dict]) -> Dict:
    """Compute totals, percentages per category, and simple anomaly flags."""
    totals = defaultdict(float)
    overall = 0.0
    prices = []
    for it in items:
        # prefer explicit line_total if parser provided it
        if it.get("line_total") is not None:
            line_total = float(it.get("line_total", 0.0))
        else:
            line_total = float(it.get("price", 0.0)) * max(1, it.get("quantity", 1))
        totals[it.get("category", "other")] += line_total
        overall += line_total
        prices.append(line_total)

    category_percent = {k: (v / overall * 100) if overall else 0.0 for k, v in totals.items()}

    mean_price = sum(prices) / len(prices) if prices else 0.0
    anomalies = {"overspent_categories": [], "expensive_items": []}
    for cat, pct in category_percent.items():
        if pct > 40.0:
            anomalies["overspent_categories"].append({"category": cat, "pct": round(pct, 1)})

    for it in items:
        line_total = it.get("price", 0.0) * max(1, it.get("quantity", 1))
        if mean_price and line_total > mean_price * 2.5:
            anomalies["expensive_items"].append({"name": it.get("name"), "total": line_total})

    return {
        "overall_total": round(overall, 2),
        "category_totals": {k: round(v, 2) for k, v in totals.items()},
        "category_percent": {k: round(v, 1) for k, v in category_percent.items()},
        "anomalies": anomalies,
    }
