# API operations

## Commands

```text
auth status
creatives search [filters] [--limit N] [--cursor CURSOR]
                         [--all-pages --max-pages N]
creatives get LIBRARY_ID [--detail-grant GRANT]
creatives instances LIBRARY_ID --detail-grant GRANT
                              [--limit N] [--cursor CURSOR]
                              [--all-pages --max-pages N]
categories list
api capabilities
api usage
api openapi
```

Use global `--compact` for compact JSON and `--jsonl` for paginated streams.
Use `--response-meta` to include observed rate-limit headers. Use
`--env-file PATH` when configuration is not in `./.env`.

## REST mapping

| Command | Request |
|---|---|
| `auth status` | Local configuration check; no request |
| `api capabilities` | `GET /api/v1/capabilities` |
| `creatives search` | `GET /api/v1/creatives` |
| `creatives get` | `GET /api/v1/creatives/{libraryId}` |
| `creatives instances` | `GET /api/v1/creatives/{libraryId}/instances` |
| `categories list` | `GET /api/v1/categories` |
| `api usage` | `GET /api/v1/usage` |
| `api openapi` | `GET /api/v1/openapi.json` |

Authenticate with `Authorization: Bearer $ADWALL_API_KEY`. Use
`ADWALL_BASE_URL=https://adwall.io/api` unless the environment explicitly
overrides it. Append the OpenAPI path `/api/v1/...`; the resulting official
search URL is `https://adwall.io/api/api/v1/creatives`. Preserve the repeated
`/api`.

## Detail grant

Read `libraryId` and `detailGrant` from a search item. Pass the grant only with
that same `libraryId`; the CLI maps `--detail-grant` to
`X-AdWall-Detail-Grant`.

Always pass the grant to `creatives get` when detail follows search. Require it
for `creatives instances`. Reusing the search grant prevents another charge for
the related detail/instances request.

## Pagination and limits

Set `--limit` between 1 and 50. Pass the response's `nextCursor` as `--cursor`.
Use `--all-pages --max-pages N` only for a bounded automatic traversal.

Treat 60 requests per minute as an observed operational ceiling. On `429`,
honor the server retry interval. Stop on subscription, quota, and access errors.

## Sorting and discovery

Expect newest-first ordering by default. Use reach sorting only for EU
creatives. Query `api capabilities` for supported values, `categories list`
for category IDs, `api usage` before broad pagination, and `api openapi` when
the bundled v1.1.0 snapshot may be stale.
