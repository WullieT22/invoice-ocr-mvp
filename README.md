# Invoice OCR MVP

## Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open: http://127.0.0.1:8000

## Optional: enable LLM extraction
Set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, default `gpt-4.1-mini`) to enable AI extraction. If not set, the app uses the regex extractor.

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4.1-mini"
```

## Demo AI extraction on text
```bash
python scripts/extract_demo.py path/to/invoice.txt
```
