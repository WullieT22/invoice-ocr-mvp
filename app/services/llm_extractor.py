import json
import os
from typing import Any

from openai import OpenAI

SUPPORTED_FIELDS = {
    "invoice_number",
    "po_number",
    "vendor_name",
    "invoice_date",
    "due_date",
    "subtotal",
    "tax",
    "total",
    "currency",
    "line_items",
}


def extract_invoice_fields_llm(text: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You extract invoice fields from OCR text. "
        "Return a JSON object only, with keys: invoice_number, po_number, vendor_name, "
        "invoice_date (YYYY-MM-DD), due_date (YYYY-MM-DD), subtotal, tax, total, currency (ISO), "
        "line_items (array of objects with description, quantity, unit_price, amount). "
        "Use null for unknowns and numbers for monetary fields."
    )

    user_prompt = f"Extract invoice fields from this OCR text:\n\n{text[:12000]}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None

    return _normalize_payload(payload)


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {key: payload.get(key) for key in SUPPORTED_FIELDS}

    line_items = payload.get("line_items")
    if not isinstance(line_items, list):
        line_items = []
    normalized["line_items"] = [
        {
            "description": item.get("description"),
            "quantity": _to_number(item.get("quantity")),
            "unit_price": _to_number(item.get("unit_price")),
            "amount": _to_number(item.get("amount")),
        }
        for item in line_items
        if isinstance(item, dict)
    ]

    for field in ("subtotal", "tax", "total"):
        normalized[field] = _to_number(normalized.get(field))

    return normalized


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
