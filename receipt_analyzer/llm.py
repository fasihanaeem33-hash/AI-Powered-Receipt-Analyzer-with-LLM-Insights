import os
import json
from typing import Dict, List


def _build_prompt(items: List[Dict], analysis: Dict) -> str:
    lines = [f"Items (name | qty | price):"]
    for it in items:
        lines.append(f"- {it.get('name')} | {it.get('quantity',1)} | {it.get('price')}")
    lines.append("")
    lines.append(f"Totals: {json.dumps(analysis.get('category_totals', {}))}")
    lines.append(f"Overall: {analysis.get('overall_total')}")
    lines.append("")
    lines.append("Provide concise, actionable budgeting advice and highlight overspending or anomalies.")
    return "\n".join(lines)


def generate_advice(items: List[Dict], analysis: Dict) -> str:
    """Attempt to call OpenAI if key present, otherwise return a heuristic advice string."""
    key = os.environ.get("OPENAI_API_KEY")
    prompt = _build_prompt(items, analysis)
    if key:
        try:
            import openai

            openai.api_key = key
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "system", "content": "You are a helpful financial assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=400,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # fall through to heuristic
            pass

    # Heuristic fallback
    adv = ["Budgeting advice:"]
    overall = analysis.get("overall_total", 0.0)
    if overall == 0:
        adv.append("No spend detected.")
        return "\n".join(adv)

    adv.append(f"You spent ${overall:.2f} in this receipt.")
    overs = analysis.get("anomalies", {}).get("overspent_categories", [])
    if overs:
        adv.append("High spending categories:")
        for o in overs:
            adv.append(f"- {o['category']}: {o['pct']}% of total")
        adv.append("Consider reducing frequency or choosing cheaper substitutes in these categories.")
    else:
        adv.append("No major overspending by category detected.")

    expensive = analysis.get("anomalies", {}).get("expensive_items", [])
    if expensive:
        adv.append("Items that stand out as expensive:")
        for it in expensive:
            adv.append(f"- {it['name']}: ${it['total']:.2f}")

    adv.append("Try setting a weekly budget per category and track receipts to detect trends.")
    return "\n".join(adv)
