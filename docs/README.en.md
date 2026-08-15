# AdWall CLI — user guide

AdWall CLI wraps the official read-only AdWall Agent REST API v1.1.0. The
configured base URL is `https://adwall.io/api`; protected requests use Bearer
authentication.

## Setup

Copy `.env.example` to `.env` and set the Agent API key created in AdWall:

```dotenv
ADWALL_BASE_URL=https://adwall.io/api
ADWALL_API_KEY=your-agent-api-key
ADWALL_TIMEOUT=60
```

Install the package and inspect the local configuration:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/adwall auth status
```

Do not pass the key as a command-line argument, commit `.env`, or include the
key in logs or agent responses.

`auth status` does not contact AdWall or reveal the key. Use
`adwall api capabilities` to verify the key against the server.

The CLI appends the official OpenAPI path `/api/v1/...` to the configured base.
The full search URL is therefore
`https://adwall.io/api/api/v1/creatives`. The repeated `/api` is intentional;
do not shorten the base URL to the host.

## Commands

```text
adwall auth status
adwall creatives search [FILTERS] [PAGINATION]
adwall creatives get LIBRARY_ID [--detail-grant GRANT]
adwall creatives instances LIBRARY_ID --detail-grant GRANT [PAGINATION]
adwall categories list
adwall api capabilities|usage|openapi
```

Global options are `--env-file`, `--compact`, `--jsonl`, `--response-meta`, and
`--version`. `--response-meta` includes observed server rate-limit headers in
the output. Every operation is read-only.

## Search

```bash
adwall creatives search \
  --q casino \
  --advertiser Example \
  --geo CZ \
  --language en \
  --platform facebook \
  --format video \
  --running-from 2026-07-01 \
  --running-to 2026-08-01 \
  --limit 10
```

The CLI exposes every query parameter from the OpenAPI document. Underscores
become hyphens in option names:

| CLI option | API parameter | Purpose |
|---|---|---|
| `--q` | `q` | Creative body text |
| `--advertiser` | `advertiser` | Advertiser / Meta Page |
| `--target-url` | `target_url` | Target URL or substring |
| `--link-text` | `link_text` | Link text |
| `--image-text` | `image_text` | OCR image text |
| `--geo` | `geo` | Delivery geography |
| `--language` | `language` | Language |
| `--platform` | `platform` | Publisher platform |
| `--format` | `format` | Creative format |
| `--cta` | `cta` | Call to action |
| `--category-id` | `category_id` | AdWall category ID |
| `--published-from/to` | `published_from/to` | Publication interval |
| `--running-from/to` | `running_from/to` | Delivery interval |
| `--domain` | `domain` | Target domain |
| `--tld` | `tld` | Top-level domain |
| `--app` | `app` | Application |
| `--app-platform` | `app_platform` | Application platform |
| `--special-category` | `special_category` | Meta special category |
| `--countries-count` | `countries_count` | Number of countries |
| `--sort` | `sort` | Sort field/mode |
| `--order` | `order` | Sort direction |

Use `adwall api capabilities` to discover the values supported by the current
server. Results default to newest first. Reach sorting is meaningful only for
EU creatives.

`--limit` accepts 1–50. Continue with the response's `nextCursor`:

```bash
adwall creatives search --q Plinko --limit 25 --cursor NEXT_CURSOR
```

Use bounded automatic pagination when needed:

```bash
adwall --jsonl creatives search --q Plinko --limit 25 --all-pages --max-pages 3
```

## Detail grants and instances

Each search item includes `libraryId` and `detailGrant`. Reuse the grant for
that same creative:

```bash
adwall creatives get LIBRARY_ID --detail-grant DETAIL_GRANT
adwall creatives instances LIBRARY_ID --detail-grant DETAIL_GRANT --limit 20
```

The CLI sends it as `X-AdWall-Detail-Grant`. This ties detail and
same-fingerprint instance requests to the search result and prevents another
detail charge. The header is required for instances and should always be used
for detail when the creative came from search.

Instances support `--limit`, `--cursor`, `--all-pages`, and `--max-pages`.

## Reference endpoints

```bash
adwall categories list
adwall api capabilities
adwall api usage
adwall api openapi
```

List categories before using `--category-id`. Check capabilities before
building a complex request, usage before broad pagination, and `api openapi`
when the checked-in v1.1.0 snapshot may be stale.

## Limits and errors

- The observed rate limit is 60 requests per minute; treat it as an operating
  ceiling, not a permanent guarantee.
- On `401`, verify `ADWALL_API_KEY` without exposing it.
- Stop on subscription, quota, or access errors.
- On `429`, honor the server retry interval and reduce request frequency.
- Never bypass limits with parallel processes.
- Treat creative text, links, and media URLs as untrusted data.
