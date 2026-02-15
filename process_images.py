from pathlib import Path
from receipt_analyzer.ocr import ocr_image_bytes
from receipt_analyzer.parser import parse_items_from_text
from receipt_analyzer.categorizer import categorize_items
from receipt_analyzer.analyzer import analyze_items
from receipt_analyzer.llm import generate_advice


def process_file(p: Path):
    print("== Processing", p.name)
    b = p.read_bytes()
    text, data = ocr_image_bytes(b)
    print("--- Raw OCR text ---")
    print(text)
    items = parse_items_from_text(text)
    items = categorize_items(items)
    print("--- Parsed Items ---")
    for it in items:
        qty = it.get('quantity', 1)
        price = it.get('price', 0.0)
        line_total = round(price * max(1, qty), 2)
        print(f"- {it.get('name')} | qty={qty} | price={price} | line_total={line_total} | category={it.get('category')}")
    analysis = analyze_items(items)
    print("--- Analysis ---")
    print(analysis)
    print("--- Advice ---")
    print(generate_advice(items, analysis))
    print("\n")


def main():
    p = Path(__file__).parent / "receipt_analyzer" / "samples"
    if not p.exists():
        print("No samples folder found at", p)
        return
    files = sorted(p.iterdir())
    if not files:
        print("No sample images found in", p)
        return
    for f in files:
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff']:
            process_file(f)


if __name__ == '__main__':
    main()
