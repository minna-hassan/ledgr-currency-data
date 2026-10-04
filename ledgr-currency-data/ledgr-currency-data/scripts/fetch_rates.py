"""Provider-neutral LEDGR FX fetch entry point.

Intentionally fails closed until a provider is approved for the app's
intended use and redistribution model. Never commit API credentials here.
"""

def main() -> None:
    raise SystemExit(
        "No approved FX provider configured. Do not publish unverified rates."
    )

if __name__ == "__main__":
    main()
