from receipt_analyzer.parser import parse_items_from_text


def test_basic_parse():
    sample = """
    Apples 2 x 1.50
    Bread 2.00
    Milk 3.50
    Total 8.50
    """
    items = parse_items_from_text(sample)
    assert any(i['name'].lower().startswith('apples') for i in items)
    assert any(i['name'].lower().startswith('bread') for i in items)
    total = sum(i['price'] * i.get('quantity', 1) for i in items)
    assert abs(total - 7.0) < 0.01
