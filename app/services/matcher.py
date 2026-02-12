from difflib import SequenceMatcher


STUB_PO_DATA = {
    "PO-1001": {"vendor_name": "Acme Supplies", "total": 1250.00},
    "45001234": {"vendor_name": "Contoso Manufacturing", "total": 489.50},
    "PO-7788": {"vendor_name": "Northwind Traders", "total": 1049.99},
}


def match_invoice(invoice_data):
    po_number = invoice_data.get("po_number")
    vendor_name = invoice_data.get("vendor_name")
    total = invoice_data.get("total")

    if not po_number:
        return {
            "status": "needs_review",
            "message": "Missing PO number",
            "confidence": 0.2,
        }

    po_record = STUB_PO_DATA.get(po_number)
    if not po_record:
        return {
            "status": "pending",
            "message": f"PO {po_number} not found in Epicor stub",
            "confidence": 0.3,
        }

    vendor_score = _similarity(vendor_name, po_record.get("vendor_name"))
    total_score = _total_score(total, po_record.get("total"))
    confidence = round((vendor_score + total_score) / 2, 2)

    status = "matched" if confidence >= 0.7 else "needs_review"
    message = "Matched to Epicor stub" if status == "matched" else "Possible match, verify totals/vendor"

    return {
        "status": status,
        "message": message,
        "confidence": confidence,
        "po_record": po_record,
    }


def _similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.4
    return round(SequenceMatcher(None, left.lower(), right.lower()).ratio(), 2)


def _total_score(actual: float | None, expected: float | None) -> float:
    if actual is None or expected is None:
        return 0.4
    if expected == 0:
        return 0.4
    delta = abs(actual - expected)
    return max(0.0, round(1 - (delta / expected), 2))
