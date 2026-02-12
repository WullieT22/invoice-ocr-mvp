import io
import pdfplumber
import pandas as pd
from docx import Document
from PIL import Image
import pytesseract

from services.ai_extractor import extract_invoice_fields, estimate_extraction_confidence
from services.llm_extractor import extract_invoice_fields_llm

async def extract_invoice_data(file):
    filename = file.filename.lower()
    content = await file.read()

    text = ""

    if filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif filename.endswith((".png", ".jpg", ".jpeg", ".tiff")):
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img)

    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(content))
        text = df.to_string(index=False)

    llm_extracted = extract_invoice_fields_llm(text)
    regex_extracted = extract_invoice_fields(text)

    if llm_extracted:
        merged = _merge_extractions(llm_extracted, regex_extracted)
        merged["extraction_confidence"] = estimate_extraction_confidence(merged)
        extracted = merged
    else:
        extracted = regex_extracted

    return {
        "raw_text": text[:2000],
        **extracted,
    }


def _merge_extractions(primary: dict, fallback: dict) -> dict:
    merged = dict(fallback)
    for key, value in primary.items():
        if key == "line_items":
            merged[key] = value or fallback.get(key, [])
            continue
        if value is not None and value != "":
            merged[key] = value
    return merged
