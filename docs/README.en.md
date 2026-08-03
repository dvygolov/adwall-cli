# AdWall CLI — user guide

AdWall CLI exposes the GraphQL APIs used by the first-party AdWall web app. It
is unofficial and may change without notice.

## Setup

Copy `.env.example` to `.env`, set `ADWALL_EMAIL` and `ADWALL_PASSWORD`, install
the package, then create an isolated CLI session:

```bash
python -m venv .venv
.venv/bin/pip install .
.venv/bin/adwall auth login
.venv/bin/adwall creatives search --query casino --country CZ --limit 10
```

The password stays in `.env`. The session file contains only access and refresh
tokens and is ignored by Git. The client renews expired tokens once.

## Commands

```text
auth login|status|logout
creatives search|get
dictionaries categories|countries|languages
favorites list|add|remove|toggle
blacklist rules|direct|affected|add-rule|remove-rule|clear-ad
apps search
archives list|create|retry
raw ENDPOINT QUERY_FILE
```

Run `adwall creatives search --help` for the complete `AdsFilterInput` mapping.
Repeated list options accept either repeated flags or comma-separated values.
Use `--all-pages --max-pages N` deliberately because unique ad retrievals may
count against the account plan. Every mutation requires `--yes`.

Never expose `.env`, the session file, passwords, browser storage, browser
cookies, access tokens, or refresh tokens. Do not bypass CAPTCHA, quotas,
subscriptions, rate limits, or access controls.
