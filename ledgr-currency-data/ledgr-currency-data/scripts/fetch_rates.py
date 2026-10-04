
import json
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

REQUIRED_CURRENCIES = {
    "USD", "PKR", "EUR", "GBP", "AED", "SAR",
    "JPY", "CNY", "INR", "CAD", "AUD",
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LEDGR-CurrencyData/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    if not API_KEY:
        sys.exit("Missing EXCHANGERATE_API_KEY environment variable.")

    url = f"{BASE_URL}/{API_KEY}/latest/USD"

    try:
        response = fetch_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        sys.exit(f"ExchangeRate-API request failed: {exc}")

    if response.get("result") != "success":
        sys.exit(
            "ExchangeRate-API returned an unsuccessful result: "
            + str(response.get("error-type", "unknown error"))
        )

    provider_rates = response.get("conversion_rates")
    if not isinstance(provider_rates, dict):
        sys.exit("Response does not contain conversion_rates.")

    rates = {"USD": 1.0}

    for code, value in provider_rates.items():
        if (
            isinstance(code, str)
            and len(code) == 3
            and code.isalpha()
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
        ):
            rates[code.upper()] = float(value)

    missing = sorted(REQUIRED_CURRENCIES - rates.keys())
    if missing:
        sys.exit("Missing required currencies: " + ", ".join(missing))

    snapshot = {
        "schemaVersion": 1,
        "status": "ok",
        "base": "USD",
        "date": response.get("time_last_update_utc", "")[:16],
        "fetchedAt": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "source": "ExchangeRate-API",
        "rates": rates,
    }


    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT)

    print(
        f"Fetched {len(rates)} currencies. "
        f"Provider update: {snapshot['date']}"
    )


if __name__ == "__main__":
    main()
