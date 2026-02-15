# AI-Powered Receipt Analyzer

"You don't have to see the whole staircase, just take the first step."

Overview
- OCR receipts, parse items, categorize expenses, analyze spending, and generate budgeting advice via an LLM (with fallback).

Quickstart
1. Install system dependency: Tesseract OCR (required by `pytesseract`). On Windows install from: https://github.com/tesseract-ocr/tesseract
2. Create a venv and install Python deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. (Optional) Set `OPENAI_API_KEY` in environment to enable LLM-generated advice.

4. Run the Streamlit demo:

```bash
streamlit run app.py
```

Notes
- If no `OPENAI_API_KEY` is present, the app will produce a heuristic, template-based financial advice fallback.
- For best OCR results, use clear photos/scans and ensure Tesseract is installed and on your PATH.

Files
- `receipt_analyzer/ocr.py`: image preprocessing + OCR wrapper
- `receipt_analyzer/parser.py`: text -> structured items
- `receipt_analyzer/categorizer.py`: simple keyword-based categories
- `receipt_analyzer/analyzer.py`: totals, percentages, anomaly detection
- `receipt_analyzer/llm.py`: OpenAI integration with fallback advice
- `app.py`: Streamlit demo interface
- `tests/`: basic unit test for parser