import json
import sys
from pathlib import Path

from app.services.ai_extractor import extract_invoice_fields


def main() -> int:
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("Provide text via stdin or pass a text file path.")
        return 1

    extracted = extract_invoice_fields(text)
    print(json.dumps(extracted, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
