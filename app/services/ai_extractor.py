import re
from datetime import datetime
from typing import Any

CURRENCY_SYMBOLS = "£$€"

INVOICE_NUMBER_PATTERNS = [
    r"Invoice\s*(?:No|#|Number)\s*[:\s]*([A-Z0-9-]+)",
    r"Inv\s*#\s*([A-Z0-9-]+)",
]

PO_NUMBER_PATTERNS = [
    r"PO\s*(?:No|#|Number)?\s*[:\s]*([A-Z0-9-]+)",
    r"Purchase\s*Order\s*(?:No|#|Number)?\s*[:\s]*([A-Z0-9-]+)",
]

DATE_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2})",
    r"(\d{2}/\d{2}/\d{4})",
    r"(\d{2}-\d{2}-\d{4})",
]

AMOUNT_PATTERN = r"([£$€]?\s*\d[\d,]*\.\d{2})"

LINE_ITEM_PATTERN = re.compile(
    r"^(?P<description>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+(?P<unit>[£$€]?\s*\d[\d,]*\.\d{2})\s+(?P<amount>[£$€]?\s*\d[\d,]*\.\d{2})$"
)


def extract_invoice_fields(text: str) -> dict[str, Any]:
    cleaned_text = text or ""
    invoice_number = _find_first(INVOICE_NUMBER_PATTERNS, cleaned_text)
    po_number = _find_first(PO_NUMBER_PATTERNS, cleaned_text)
    vendor_name = _extract_vendor(cleaned_text)
    invoice_date = _extract_labeled_date(r"invoice\s*date", cleaned_text)
    due_date = _extract_labeled_date(r"due\s*date", cleaned_text)

    subtotal = _extract_labeled_amount("subtotal", cleaned_text)
    tax = _extract_labeled_amount("tax", cleaned_text)
    total = _extract_labeled_amount(r"total|amount\s*due|balance\s*due", cleaned_text)

    currency = _detect_currency(cleaned_text)
    line_items = _extract_line_items(cleaned_text)

    extracted = {
        "invoice_number": invoice_number,
        "po_number": po_number,
        "vendor_name": vendor_name,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "currency": currency,
        "line_items": line_items,
    }

    extracted["extraction_confidence"] = _estimate_confidence(extracted)
    return extracted


def _find_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _find_last(pattern: str, text: str) -> str | None:
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    if not matches:
        return None
    return matches[-1].strip()


def _extract_vendor(text: str) -> str | None:
    for pattern in [r"Vendor\s*[:\s]+(.+)", r"From\s*[:\s]+(.+)", r"Supplier\s*[:\s]+(.+)"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        return lines[0][:120]
    return None


def _extract_labeled_date(label_pattern: str, text: str) -> str | None:
    label_match = re.search(label_pattern + r"\s*[:\s]*([\w/-]+)", text, flags=re.IGNORECASE)
    if label_match:
        date_candidate = label_match.group(1)
        parsed = _normalize_date(date_candidate)
        if parsed:
            return parsed

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            parsed = _normalize_date(match.group(1))
            if parsed:
                return parsed
    return None


def _normalize_date(date_str: str) -> str | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.date().isoformat()
        except ValueError:
            continue
    return None


def _extract_labeled_amount(label_pattern: str, text: str) -> float | None:
    match = _find_last(rf"(?:{label_pattern})\s*[:\s]*{AMOUNT_PATTERN}", text)
    if not match:
        return None
    return _parse_amount(match)


def _parse_amount(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    cleaned = cleaned.lstrip(CURRENCY_SYMBOLS).strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _detect_currency(text: str) -> str | None:
    if "£" in text:
        return "GBP"
    if "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    return None


def _extract_line_items(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = LINE_ITEM_PATTERN.match(line)
        if not match:
            continue
        items.append({
            "description": match.group("description").strip(),
            "quantity": _parse_amount(match.group("qty")),
            "unit_price": _parse_amount(match.group("unit")),
            "amount": _parse_amount(match.group("amount")),
        })
        if len(items) >= 25:
            break
    return items


def _estimate_confidence(extracted: dict[str, Any]) -> float:
    key_fields = [
        extracted.get("invoice_number"),
        extracted.get("po_number"),
        extracted.get("vendor_name"),
        extracted.get("invoice_date"),
        extracted.get("total"),
    ]
    found = sum(1 for field in key_fields if field)
    return round(found / len(key_fields), 2)
