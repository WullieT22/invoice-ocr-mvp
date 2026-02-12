import io
import pdfplumber
import pandas as pd
from docx import Document
from PIL import Image
import pytesseract

from services.ai_extractor import extract_invoice_fields

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

    extracted = extract_invoice_fields(text)
    return {
        "raw_text": text[:2000],
        **extracted,
    }
