import re
from typing import List, Dict


NUM_RE = re.compile(r"\d+[\d,\.]*")


def _clean_num(token: str) -> float:
    if token is None:
        return 0.0
    s = token.replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        return 0.0


HEADER_FOOTER_PATTERNS = [
    r"invoice", r"date", r"cash", r"cashier", r"phone", r"thank", r"subtotal",
    r"grand total", r"total", r"gst", r"amount paid", r"change", r"payment",
    r"time", r"wednesday", r"monday", r"tuesday", r"thursday", r"friday", r"saturday", r"sunday",
    r"january", r"february", r"march", r"april", r"may", r"june", r"july", r"august", r"september", r"october", r"november", r"december",
    r"am", r"pm",
]


def _is_date_or_time(line: str) -> bool:
    """Check if line contains date/time patterns (like '11:37 AM', 'Feb 2026', etc)."""
    s = line.lower()
    # check for time patterns (HH:MM AM/PM)
    if ':' in s and ('am' in s or 'pm' in s):
        return True
    # check for year patterns (like 2026, 2025, etc)
    if any(f"{year}" in s for year in range(2000, 2050)):
        return True
    # check for month abbreviations
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    if any(m in s for m in months):
        return True
    return False


def _is_header_footer(line: str) -> bool:
    s = line.lower()
    # skip lines that are clearly not item lines
    for p in HEADER_FOOTER_PATTERNS:
        if p in s:
            return True
    # skip lines that are long numeric sequences (phone numbers, invoice ids)
    nums = NUM_RE.findall(line)
    for n in nums:
        if len(n.replace(',', '').replace('.', '')) >= 7:
            return True
    return False


def parse_items_from_text(text: str) -> List[Dict]:
    """Parse OCR text into items with `name`, `quantity`, `rate`, and `amount`.

    Heuristics:
    - Skip header/footer lines and date/time lines.
    - Use numeric tokens: treat last numeric token as `amount`, previous as `rate`, first numeric token as `quantity` when sensible.
    - If only rate and qty present, compute line_total = rate * qty.
    - If amount present, use it as line_total.
    """
    items: List[Dict] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if _is_header_footer(line):
            continue
        if _is_date_or_time(line):
            continue
        # skip lines that are just numbers (likely totals or standalone amounts)
        if re.match(r'^[\d\.,\s]+$', line):
            continue
        nums = NUM_RE.findall(line)
        if not nums:
            continue

        # Heuristic: last numeric token is amount
        amount = _clean_num(nums[-1]) if nums else 0.0
        rate = None
        qty = 1

        if len(nums) >= 2:
            # rate is second last
            rate = _clean_num(nums[-2])
        if len(nums) >= 3:
            # qty could be first numeric token
            maybe_qty = _clean_num(nums[0])
            # treat as qty if small and not likely an id (<=1000)
            if 0 < maybe_qty <= 1000:
                qty = int(maybe_qty) if float(maybe_qty).is_integer() else maybe_qty

        # compute line_total and unit price (`price`)
        if amount and amount > 0:
            line_total = round(amount, 2)
            # try unit price: amount divided by qty if qty meaningful
            try:
                unit_price = round(line_total / float(qty), 2) if qty else None
            except Exception:
                unit_price = None
        elif rate and rate > 0:
            # treat rate as unit price
            unit_price = round(rate, 2)
            line_total = round(unit_price * (qty or 1), 2)
        else:
            unit_price = None
            line_total = 0.0

        # derive name by removing numeric tokens and common separators
        name_part = re.sub(NUM_RE, '', line).strip(' -:,.')
        name = re.sub(r"\b(kg|g|dozen|x|pcs|pc|tab|tabnet)\b", '', name_part, flags=re.IGNORECASE).strip()
        if not name:
            name = 'UNKNOWN'

        items.append({
            'name': name,
            'quantity': qty,
            'rate': round(rate, 2) if rate else None,
            'price': unit_price if unit_price is not None else 0.0,
            'line_total': line_total,
            'amount': line_total,
        })

    return items
