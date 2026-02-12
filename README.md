# Invoice OCR MVP

## Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open: http://127.0.0.1:8000

## Demo AI extraction on text
```bash
python scripts/extract_demo.py path/to/invoice.txt
```
