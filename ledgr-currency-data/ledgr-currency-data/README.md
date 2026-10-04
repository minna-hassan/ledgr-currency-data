
# LEDGR Currency Data

Automated exchange-rate data infrastructure for LEDGR, a multi-currency
personal finance and budgeting application built with Flutter.

## Overview

This repository maintains a normalized snapshot of exchange rates using
ExchangeRate-API and GitHub Actions.

The intended pipeline is:

1. Fetch the provider's latest USD-based exchange rates.
2. Validate the response and reject malformed or stale data.
3. Publish the validated snapshot as `data/rates.json`.
4. Allow the LEDGR Flutter app to download the snapshot and cache it locally
   using Hive.

## Data format

The snapshot uses this structure:

```json
{
  "schemaVersion": 1,
  "status": "ok",
  "base": "USD",
  "date": "YYYY-MM-DD",
  "fetchedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "source": "ExchangeRate-API",
  "rates": {
    "USD": 1,
    "PKR": 280.5,
    "EUR": 0.85
  }
}
```

The values above are illustrative only, not live exchange rates.

Each entry in `rates` represents the number of units of that currency
equivalent to one unit of the base currency, USD.

For a conversion from currency A to currency B:

`amountB = amountA / rates[A] * rates[B]`

## Currency integrity

- Use ISO 4217 currency codes such as `PKR`, `USD`, and `EUR` as currency
  identifiers.
- Never identify a currency by its symbol alone. The `$` symbol, for
  example, is used by multiple currencies.
- Preserve original transaction amounts and their currency codes.
- Exchange-rate updates must not rewrite historical transactions.
- Display symbols and decimal precision using currency metadata, not rates.

## Automation

GitHub Actions is configured to run daily and supports manual execution.

The API key is supplied through the `EXCHANGERATE_API_KEY` repository secret.
Never commit API keys or other credentials.

The workflow must validate a snapshot before committing it. If fetching or
validation fails, the previous committed snapshot should remain unchanged.

## Offline behavior

The Flutter application should:

- Validate downloaded snapshots before caching them.
- Keep the last known-good snapshot in Hive.
- Continue using cached rates when offline.
- Display the rate date and warn when data is stale.
- Show a clear error if no valid snapshot is available.

## Important limitations

Exchange rates are indicative reference values. A bank, card issuer, payment
provider, or cash exchange service may apply different rates and fees.

The repository is not a real-time trading feed and does not guarantee
transaction settlement rates.

Provider coverage, update frequency, licensing, and redistribution rights
must be checked against the applicable ExchangeRate-API plan and terms.

## Repository status

The repository and automation are being configured. The initial
`data/rates.json` file is a placeholder until a successful, validated provider
update is completed.
