# Search filters

Use `python scripts/adwall.py creatives search [options]`.

| CLI option | REST query parameter | Meaning |
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
| `--published-from` | `published_from` | Publication interval start |
| `--published-to` | `published_to` | Publication interval end |
| `--running-from` | `running_from` | Delivery interval start |
| `--running-to` | `running_to` | Delivery interval end |
| `--domain` | `domain` | Target domain |
| `--tld` | `tld` | Top-level domain |
| `--app` | `app` | Application |
| `--app-platform` | `app_platform` | Application platform |
| `--special-category` | `special_category` | Meta special category |
| `--countries-count` | `countries_count` | Number of countries |
| `--sort` | `sort` | Sort field/mode |
| `--order` | `order` | Sort direction |
| `--limit` | `limit` | Page size, 1–50 |
| `--cursor` | `cursor` | Cursor from `nextCursor` |

Use ISO-style dates such as `2026-08-15`. Query `api capabilities` instead of
guessing accepted platform, format, CTA, category, app-platform, special
category, sort, or order values.

Expect newest-first results when no sort is specified. Use reach sorting only
for EU creatives. Avoid assuming that multiple values or repeated flags are
supported unless the current capabilities/OpenAPI document says so.
