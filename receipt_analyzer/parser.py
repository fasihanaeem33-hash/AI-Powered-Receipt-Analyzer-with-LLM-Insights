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
    """Parse OCR text into items with `name`, `quantity`, `price`, and `amount`.

    Format: Name ... Qty ... UnitPrice ... Total
    Strategy: 
    - Last number = TOTAL amount
    - Second-to-last = UNIT PRICE
    - Quantity is inferred: total / unit_price
    """
    items: List[Dict] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if _is_header_footer(line):
            continue
        if _is_date_or_time(line):
            continue
        # skip lines that are just numbers
        if re.match(r'^[\d\.,\s%]+$', line):
            continue
        
        nums = NUM_RE.findall(line)
        if len(nums) < 2:  # need at least unit_price and total
            continue
        
        # filter out very large numbers (>10000)
        nums = [n for n in nums if _clean_num(n) < 10000]
        if len(nums) < 2:
            continue

        # Last number = TOTAL, Second-to-last = UNIT PRICE
        line_total = _clean_num(nums[-1])
        unit_price = _clean_num(nums[-2])
        
        # both must be positive
        if line_total <= 0 or unit_price <= 0:
            continue
        
        # infer quantity: total / unit_price
        try:
            qty = round(line_total / unit_price, 2)
            if qty > 100 or qty <= 0:
                qty = 1
        except:
            qty = 1
        
        line_total = round(line_total, 2)
        unit_price = round(unit_price, 2)

        # extract name: remove all numbers and category/unit words
        name_part = re.sub(NUM_RE, '', line).strip(' -:,.')
        name = re.sub(r"\b(kg|g|dozen|x|pcs|pc|tab|tabnet|dairy|meat|snacks|bakery|fruits|produce|pharmacy|beverage|%)\b", '', name_part, flags=re.IGNORECASE).strip()
        if not name or len(name) < 2:
            continue

        items.append({
            'name': name,
            'quantity': qty,
            'rate': unit_price,
            'price': unit_price,
            'line_total': line_total,
            'amount': line_total,
        })

    return items
