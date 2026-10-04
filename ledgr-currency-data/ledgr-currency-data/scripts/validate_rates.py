"""Validate the normalized LEDGR rate snapshot."""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "rates.json"
REQUIRED = {"USD", "PKR", "EUR", "GBP", "AED", "SAR", "JPY", "CNY", "INR", "CAD", "AUD"}

def fail(message: str) -> None:
    print(f"VALIDATION ERROR: {message}")
    sys.exit(1)

def main() -> None:
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read JSON: {exc}")

    if data.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    if data.get("status") != "ok":
        fail("Snapshot is not marked status=ok")
    if data.get("base") != "USD":
        fail("base must be USD")

    try:
        date.fromisoformat(data["date"])
    except (KeyError, TypeError, ValueError):
        fail("date must be a valid YYYY-MM-DD date")

    try:
        datetime.fromisoformat(data["fetchedAt"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError):
        fail("fetchedAt must be an ISO-8601 timestamp")

    if not isinstance(data.get("source"), str) or not data["source"].strip():
        fail("source must identify the provider")

    rates = data.get("rates")
    if not isinstance(rates, dict):
        fail("rates must be an object")

    for code, value in rates.items():
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code):
            fail(f"invalid currency code: {code!r}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"rate for {code} must be numeric")
        if value <= 0:
            fail(f"rate for {code} must be positive")

    missing = sorted(REQUIRED - set(rates))
    if missing:
        fail("missing required currencies: " + ", ".join(missing))
    if rates.get("USD") != 1:
        fail("USD rate must equal exactly 1")

    print(f"OK: {len(rates)} rates validated for {data['date']}")

if __name__ == "__main__":
    main()
