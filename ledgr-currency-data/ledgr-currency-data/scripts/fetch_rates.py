
import json
import math
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "rates.json"

API_KEY = os.environ.get("EXCHANGERATE_API_KEY", "").strip()
BASE_URL = "https://v6.exchangerate-api.com/v6"
TIMEOUT_SECONDS = 30

REQUIRED_CURRENCIES = {
    "USD", "PKR", "EUR", "GBP", "AED", "SAR",
    "JPY", "CNY", "INR", "CAD", "AUD",
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LEDGR-CurrencyData/1.0"},
    )

    with urllib.request.urlopen(
        request, timeout=TIMEOUT_SECONDS
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object.")

    return payload


def parse_provider_date(value: object) -> str:
    """Convert the provider's UTC update timestamp to YYYY-MM-DD."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Provider did not return an update timestamp.")

    try:
        parsed = datetime.strptime(
            value.strip(),
            "%a, %d %b %Y %H:%M:%S %z",
        )
    except ValueError as exc:
        raise ValueError(
            "Provider returned an invalid update timestamp."
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError("Provider timestamp must include a timezone.")

    age_seconds = (
        datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
    ).total_seconds()

    # Allow small clock differences, but reject future or very old data.
    if age_seconds < -300:
        raise ValueError("Provider update timestamp is in the future.")

    if age_seconds > 4 * 24 * 60 * 60:
        raise ValueError("Provider rates are more than 4 days old.")

    return parsed.date().isoformat()


def normalize_rates(payload: dict) -> dict:
    provider_rates = payload.get("conversion_rates")

    if not isinstance(provider_rates, dict):
        raise ValueError("Response does not contain conversion_rates.")

    rates = {}

    for code, value in provider_rates.items():
        if (
            not isinstance(code, str)
            or len(code) != 3
            or not code.isalpha()
            or not code.isascii()
        ):
            continue

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        value = float(value)

        if not math.isfinite(value) or value <= 0:
            continue

        rates[code.upper()] = value

    missing = sorted(REQUIRED_CURRENCIES - rates.keys())
    if missing:
        raise ValueError(
            "Missing required currencies: " + ", ".join(missing)
        )

    # The endpoint requested USD as base; enforce that contract.
    rates["USD"] = 1.0

    return rates


def write_snapshot(snapshot: dict) -> None:
    """Replace the snapshot atomically after all checks have passed."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")

    try:
        temporary.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(OUTPUT)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    if not API_KEY:
        sys.exit("Missing EXCHANGERATE_API_KEY environment variable.")

    url = f"{BASE_URL}/{API_KEY}/latest/USD"

    try:
        response = fetch_json(url)

        if response.get("result") != "success":
            raise ValueError(
                "ExchangeRate-API returned an unsuccessful result: "
                + str(response.get("error-type", "unknown error"))
            )

        snapshot_date = parse_provider_date(
            response.get("time_last_update_utc")
        )
        rates = normalize_rates(response)

        snapshot = {
            "schemaVersion": 1,
            "status": "ok",
            "base": "USD",
            "date": snapshot_date,
            "fetchedAt": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z"),
            "source": "ExchangeRate-API",
            "rates": rates,
        }

        write_snapshot(snapshot)

    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
        OSError,
    ) as exc:
        sys.exit(f"Rate update failed; existing snapshot preserved: {exc}")

    print(
        f"Success: fetched {len(rates)} currencies. "
        f"Provider rate date: {snapshot_date}"
    )


if __name__ == "__main__":
    main()
