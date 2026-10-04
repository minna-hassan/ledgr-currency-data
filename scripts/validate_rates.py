import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "rates.json"

MIN_CURRENCY_COUNT = 150
MAX_RATE_AGE_DAYS = 4


def fail(message: str) -> None:
    print(f"VALIDATION ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read snapshot JSON: {exc}")

    if not isinstance(data, dict):
        fail("Snapshot must be a JSON object.")

    if data.get("schemaVersion") != 1:
        fail("Unsupported schemaVersion.")

    if data.get("status") != "ok":
        fail("Snapshot is not initialized or status is not 'ok'.")

    if data.get("base") != "USD":
        fail("Snapshot base must be USD.")

    try:
        snapshot_date = date.fromisoformat(data["date"])
    except (KeyError, TypeError, ValueError):
        fail("date must be a valid YYYY-MM-DD date.")

    today = datetime.now(timezone.utc).date()
    age_days = (today - snapshot_date).days

    if age_days < 0:
        fail("Snapshot date cannot be in the future.")

    if age_days > MAX_RATE_AGE_DAYS:
        fail(f"Snapshot is stale ({age_days} days old).")

    try:
        fetched_at_text = data["fetchedAt"]
        if not isinstance(fetched_at_text, str):
            raise ValueError("fetchedAt must be a string.")

        fetched_at = datetime.fromisoformat(
            fetched_at_text.replace("Z", "+00:00")
        )

        if fetched_at.tzinfo is None:
            raise ValueError("Timezone is required.")

        fetched_at = fetched_at.astimezone(timezone.utc)
    except (KeyError, TypeError, ValueError):
        fail("fetchedAt must be a valid timezone-aware ISO timestamp.")

    now = datetime.now(timezone.utc)

    if fetched_at > now:
        fail("fetchedAt cannot be in the future.")

    if not isinstance(data.get("source"), str) or not data["source"].strip():
        fail("source must identify the provider.")

    rates = data.get("rates")

    if not isinstance(rates, dict):
        fail("rates must be a JSON object.")

    if len(rates) < MIN_CURRENCY_COUNT:
        fail(
            f"Only {len(rates)} currencies found; "
            f"at least {MIN_CURRENCY_COUNT} are required."
        )

    for code, value in rates.items():
        if not isinstance(code, str) or not re.fullmatch(
            r"[A-Z]{3}", code
        ):
            fail(f"Invalid currency code: {code!r}.")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"Rate for {code} must be numeric.")

        if not math.isfinite(value) or value <= 0:
            fail(f"Rate for {code} must be finite and positive.")

    if rates.get("USD") != 1 and rates.get("USD") != 1.0:
        fail("USD rate must equal 1.")

    print(
        f"VALID: {len(rates)} currencies; "
        f"base USD; rate date {snapshot_date}; "
        f"snapshot age {age_days} days."
    )


if __name__ == "__main__":
    main()
