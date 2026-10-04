
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "rates.json"

REQUIRED_CURRENCIES = {
    "USD", "PKR", "EUR", "GBP", "AED", "SAR",
    "JPY", "CNY", "INR", "CAD", "AUD",
}

MAX_RATE_AGE_DAYS = 4


def fail(message: str) -> None:
    print(f"VALIDATION ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read valid JSON: {exc}")

    if not isinstance(data, dict):
        fail("Snapshot must be a JSON object.")

    if data.get("schemaVersion") != 1:
        fail("schemaVersion must be 1.")

    if data.get("status") != "ok":
        fail("Snapshot status must be 'ok'.")

    if data.get("base") != "USD":
        fail("Base currency must be USD.")

    try:
        snapshot_date = date.fromisoformat(data["date"])
    except (KeyError, TypeError, ValueError):
        fail("date must be a valid YYYY-MM-DD date.")

    today_utc = datetime.now(timezone.utc).date()
    age_days = (today_utc - snapshot_date).days

    if age_days < 0:
        fail("Snapshot date cannot be in the future.")

    if age_days > MAX_RATE_AGE_DAYS:
        fail(f"Snapshot is stale: {age_days} days old.")

    try:
        fetched_at = datetime.fromisoformat(
            data["fetchedAt"].replace("Z", "+00:00")
        )
        if fetched_at.tzinfo is None:
            fail("fetchedAt must include a timezone.")
        fetched_at = fetched_at.astimezone(timezone.utc)
    except (KeyError, AttributeError, TypeError, ValueError):
        fail("fetchedAt must be a valid ISO-8601 timestamp.")

    if fetched_at > datetime.now(timezone.utc):
        fail("fetchedAt cannot be in the future.")

    if not isinstance(data.get("source"), str) or not data["source"].strip():
        fail("source must identify the rate provider.")

    rates = data.get("rates")
    if not isinstance(rates, dict):
        fail("rates must be a JSON object.")

    for code, value in rates.items():
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code):
            fail(f"Invalid ISO-style currency code: {code!r}.")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"Rate for {code} must be numeric.")

        if not math.isfinite(value) or value <= 0:
            fail(f"Rate for {code} must be finite and positive.")

    missing = sorted(REQUIRED_CURRENCIES - rates.keys())
    if missing:
        fail("Missing required currencies: " + ", ".join(missing))

    if rates.get("USD") != 1.0:
        fail("USD rate must equal 1.")

    print(
        f"VALID: {len(rates)} currencies; "
        f"snapshot date {snapshot_date}; age {age_days} days."
    )


if __name__ == "__main__":
    main()
