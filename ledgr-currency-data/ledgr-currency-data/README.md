# LEDGR Currency Data

A provider-neutral daily exchange-rate pipeline for LEDGR's multi-currency
personal-finance app.

## Current status

**Not production-ready yet.** The provider fetcher intentionally fails until
a source has been selected and its terms have been checked for LEDGR's use.
The included `data/rates.json` is only a placeholder, not live rate data.

## Design

```text
Approved FX provider
        ↓
GitHub Actions (scheduled daily or manual)
        ↓
Fetch → validate → update data/rates.json
        ↓
Flutter app → validate snapshot → Hive cache
```

## Snapshot contract

```json
{
  "schemaVersion": 1,
  "status": "ok",
  "base": "USD",
  "date": "YYYY-MM-DD",
  "fetchedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "source": "provider-name",
  "rates": {
    "USD": 1,
    "PKR": 280.5,
    "EUR": 0.85
  }
}
```

Rates mean **units of each currency per 1 USD**. Conversion from currency A
to currency B is `amountA / rates[A] * rates[B]`. The base USD rate is 1.

## Money integrity rules

- Store every amount with its ISO 4217 currency code, such as `{ amount: 3000, currencyCode: "PKR" }`.
- Symbols are for display only; never use `$`, `₨`, or another symbol as identity.
- Rate updates must never rewrite original transaction amounts.
- The app should retain the last valid local snapshot when network refresh fails.
- The UI should show the snapshot date and warn when rates become stale.
- Do not treat indicative conversion rates as guaranteed bank/card settlement rates.

## Workflow

The GitHub Action is scheduled daily at 05:17 UTC and supports manual runs.
It commits only when `data/rates.json` changes. The current fetch step exits
with an error by design, so it cannot publish invented or unapproved data.

## Before production

1. Choose a provider and confirm its current terms permit the intended use.
2. Implement its adapter in `scripts/fetch_rates.py`.
3. Add tests for malformed data, missing currencies, stale dates, and implausible jumps.
4. Validate the public raw-file access pattern and GitHub usage limits.
5. Add app-side schema, age, and numerical validation.
6. Do not put provider secrets or personal credentials in this repository.
