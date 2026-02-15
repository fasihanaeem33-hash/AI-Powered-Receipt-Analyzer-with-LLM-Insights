import streamlit as st
import pandas as pd
from io import BytesIO

from receipt_analyzer.ocr import ocr_image_bytes
from receipt_analyzer.parser import parse_items_from_text
from receipt_analyzer.categorizer import categorize_items
from receipt_analyzer.analyzer import analyze_items
from receipt_analyzer.llm import generate_advice


st.set_page_config(page_title="Receipt Analyzer", layout="wide")
st.title("AI-Powered Receipt Analyzer")
st.write("Upload a receipt image to extract items, categorize, and get budgeting advice.")

uploaded = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg", "tiff"]) 
if uploaded:
    img_bytes = uploaded.read()
    raw_text, _ = ocr_image_bytes(img_bytes)
    with st.expander("OCR Raw Text"):
        st.text_area("Text", raw_text, height=200)

    items = parse_items_from_text(raw_text)
    items = categorize_items(items)
    df = pd.DataFrame(items)
    if df.empty:
        st.warning("No items parsed from the receipt. Try a clearer image or different crop.")
    else:
        df_display = df.copy()
        df_display["line_total"] = df_display["price"] * df_display["quantity"]
        st.subheader("Parsed Items")
        st.dataframe(df_display)

        analysis = analyze_items(items)
        st.subheader("Spending Summary")
        st.write("Overall total: $", analysis.get("overall_total"))
        cat_totals = analysis.get("category_totals", {})
        st.write(cat_totals)

        st.subheader("Category Breakdown")
        if cat_totals:
            fig = pd.Series(cat_totals).plot.pie(y='x', autopct='%1.1f%%', ylabel='')
            st.pyplot(fig.figure)

        st.subheader("AI Financial Advice")
        advice = generate_advice(items, analysis)
        st.write(advice)

        st.subheader("Anomalies")
        st.json(analysis.get("anomalies", {}))
