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
    """Parse OCR text into items, handling multi-line formats.
    
    Handles formats where item info is split across multiple lines:
    - Name
    - Category/Extra info
    - Numbers (Qty, Price, Total)
    """
    items: List[Dict] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    # Filter out header/footer lines
    cleaned_lines = []
    for line in lines:
        if _is_header_footer(line):
            continue
        if _is_date_or_time(line):
            continue
        cleaned_lines.append(line)
    
    # Group lines: collect name lines until we hit numbers
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        
        # Skip lines that are just numbers
        if re.match(r'^[\d\.,\s%]+$', line):
            i += 1
            continue
        
        # Start collecting an item
        name_parts = [line]
        i += 1
        
        # Collect additional text lines (categories, units, etc)
        while i < len(cleaned_lines) and re.match(r'^[\d\.,\s%]+$', cleaned_lines[i]) == None:
            next_line = cleaned_lines[i]
            # Check if next line is text or numbers
            nums = NUM_RE.findall(next_line)
            if nums:
                # Has numbers, could be part of this item
                name_parts.append(next_line)
                break
            else:
                # Just text, add to name
                name_parts.append(next_line)
                i += 1
        
        # Now collect all consecutive number lines
        num_lines = []
        while i < len(cleaned_lines) and re.match(r'^[\d\.,\s%]+$', cleaned_lines[i]):
            num_lines.append(cleaned_lines[i])
            i += 1
        
        # Parse this item if we have name and numbers
        if name_parts and num_lines:
            full_line = ' '.join(name_parts + num_lines)
            parsed = _parse_single_item(full_line)
            if parsed:
                items.append(parsed)
        elif name_parts:
            # Try to parse name_parts as a single line
            full_line = ' '.join(name_parts)
            parsed = _parse_single_item(full_line)
            if parsed:
                items.append(parsed)
    
    return items


def _parse_single_item(line: str) -> Dict:
    """Parse a single item line into name, quantity, price, amount."""
    nums = NUM_RE.findall(line)
    if not nums:
        return None
    
    # filter out very large numbers (>10000) - likely IDs
    nums = [n for n in nums if _clean_num(n) < 10000]
    if not nums:
        return None

    # Parse based on number count
    if len(nums) >= 2:
        # Format: ... Price Total
        # Last = Total, 2nd-to-last = Unit Price
        line_total = _clean_num(nums[-1])
        unit_price = _clean_num(nums[-2])
        
        if unit_price > 0 and line_total > 0:
            # Calculate qty from total/price
            try:
                qty = round(line_total / unit_price, 2)
                if qty > 100:
                    qty = 1  # unreasonable qty
            except:
                qty = 1
        else:
            # Fallback: treat last as price
            unit_price = line_total
            qty = 1
    else:
        # Only 1 number: treat as price
        unit_price = _clean_num(nums[0])
        line_total = unit_price
        qty = 1
    
    if unit_price <= 0:
        return None
    
    line_total = round(line_total, 2)
    unit_price = round(unit_price, 2)

    # extract name: remove all numbers and category/unit words
    name_part = re.sub(NUM_RE, '', line).strip(' -:,.')
    name = re.sub(r"\b(kg|g|dozen|x|pcs|pc|tab|tabnet|dairy|meat|snacks|bakery|fruits|produce|pharmacy|beverage|%)\b", '', name_part, flags=re.IGNORECASE).strip()
    if not name or len(name) < 2:
        return None

    return {
        'name': name,
        'quantity': qty,
        'rate': unit_price,
        'price': unit_price,
        'line_total': line_total,
        'amount': line_total,
    }
