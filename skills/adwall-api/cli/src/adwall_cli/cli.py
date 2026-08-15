from __future__ import annotations

import argparse
import json
from typing import Any, Callable, Mapping

from . import __version__
from .client import AdWallClient
from .config import Settings
from .errors import AdWallError, ConfigError
from .output import configure_utf8_stdout, emit, emit_jsonl, error_payload


SEARCH_FIELDS = (
    "q",
    "advertiser",
    "target_url",
    "link_text",
    "image_text",
    "geo",
    "language",
    "platform",
    "format",
    "cta",
    "category_id",
    "published_from",
    "published_to",
    "running_from",
    "running_to",
    "domain",
    "tld",
    "app",
    "app_platform",
    "special_category",
    "countries_count",
    "sort",
    "order",
)

PLATFORMS = (
    "facebook",
    "instagram",
    "audience_network",
    "messenger",
    "whatsapp",
    "oculus",
    "threads",
)
MEDIA_FORMATS = ("image", "video", "carousel", "none")


def _add_page_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=10, help="Results per request (1-50)")
    parser.add_argument("--cursor", help="Cursor returned by the previous response")
    parser.add_argument("--all-pages", action="store_true", help="Fetch more cursor pages")
    parser.add_argument(
        "--max-pages", type=int, default=5, help="Safety cap used with --all-pages"
    )


def _add_search_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", "--q", dest="q")
    parser.add_argument("--advertiser", "--page-name", dest="advertiser")
    parser.add_argument("--target-url", "--url", dest="target_url")
    parser.add_argument("--link-text", dest="link_text")
    parser.add_argument("--image-text", dest="image_text")
    parser.add_argument("--geo", "--country", dest="geo")
    parser.add_argument("--language")
    parser.add_argument("--platform", "--placement", choices=PLATFORMS)
    parser.add_argument("--format", choices=MEDIA_FORMATS)
    parser.add_argument("--cta")
    parser.add_argument("--category-id", dest="category_id")
    parser.add_argument(
        "--published-from", "--created-from", dest="published_from", metavar="ISO_DATE"
    )
    parser.add_argument(
        "--published-to", "--created-to", dest="published_to", metavar="ISO_DATE"
    )
    parser.add_argument(
        "--running-from", "--delivery-from", dest="running_from", metavar="ISO_DATE"
    )
    parser.add_argument(
        "--running-to", "--delivery-to", dest="running_to", metavar="ISO_DATE"
    )
    parser.add_argument("--domain", "--hostname", dest="domain")
    parser.add_argument("--tld")
    parser.add_argument("--app", "--app-id", dest="app")
    parser.add_argument("--app-platform", dest="app_platform")
    parser.add_argument("--special-category", dest="special_category")
    parser.add_argument("--countries-count", type=int, dest="countries_count")
    parser.add_argument(
        "--sort", help="Official sort key; currently reach is advertised (EU-only)"
    )
    parser.add_argument("--order", choices=("asc", "desc"))


def _validate_page_args(limit: int, max_pages: int) -> None:
    if not 1 <= limit <= 50:
        raise ConfigError("--limit must be between 1 and 50")
    if max_pages <= 0:
        raise ConfigError("--max-pages must be positive")


def _clean_params(values: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in values.items()
        if value is not None and value != ""
    }


def _collect_pages(
    fetch: Callable[[str | None], dict[str, Any]],
    *,
    cursor: str | None,
    all_pages: bool,
    max_pages: int,
) -> dict[str, Any]:
    result = fetch(cursor)
    if not all_pages:
        return result

    items = list(result.get("items") or [])
    page = dict(result.get("page") or {})
    pages_fetched = 1
    while page.get("hasNextPage") and pages_fetched < max_pages:
        next_cursor = page.get("nextCursor")
        if not isinstance(next_cursor, str) or not next_cursor:
            break
        next_result = fetch(next_cursor)
        items.extend(next_result.get("items") or [])
        page = dict(next_result.get("page") or {})
        pages_fetched += 1

    result["items"] = items
    result["page"] = {**page, "pagesFetched": pages_fetched, "returned": len(items)}
    return result


def _items_for_jsonl(value: Any) -> list[Any] | None:
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return value["items"]
    if isinstance(value, list):
        return value
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adwall", description="Agent-first CLI for the official AdWall REST API."
    )
    parser.add_argument("--env-file", help="Path to .env (default: ./.env)")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    parser.add_argument("--jsonl", action="store_true", help="Emit response items as JSONL")
    parser.add_argument(
        "--response-meta",
        action="store_true",
        help="Wrap data with observed rate-limit response headers",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    auth = commands.add_parser("auth", help="Inspect local API-key configuration")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)
    auth_sub.add_parser("status")

    creatives = commands.add_parser("creatives", aliases=["creative"])
    creative_sub = creatives.add_subparsers(dest="creative_command", required=True)
    search = creative_sub.add_parser("search")
    _add_search_filters(search)
    _add_page_args(search)

    get_creative = creative_sub.add_parser("get")
    get_creative.add_argument("library_id")
    get_creative.add_argument(
        "--detail-grant",
        help="detailGrant from search; avoids charging the same creative again",
    )

    instances = creative_sub.add_parser("instances")
    instances.add_argument("library_id")
    instances.add_argument(
        "--detail-grant", required=True, help="detailGrant returned by search"
    )
    _add_page_args(instances)

    categories = commands.add_parser("categories", aliases=["category"])
    category_sub = categories.add_subparsers(dest="category_command", required=True)
    category_sub.add_parser("list")

    api = commands.add_parser("api", help="Inspect official API metadata")
    api_sub = api.add_subparsers(dest="api_command", required=True)
    api_sub.add_parser("capabilities")
    api_sub.add_parser("usage")
    api_sub.add_parser("openapi")
    return parser


def execute(args: argparse.Namespace, client: AdWallClient) -> Any:
    if args.command == "auth":
        settings = client.settings
        return {
            "configured": bool(settings.api_key),
            "baseUrl": settings.base_url,
            "envFile": str(settings.env_file) if settings.env_file else None,
        }

    if args.command in ("creatives", "creative"):
        if args.creative_command == "search":
            _validate_page_args(args.limit, args.max_pages)
            base_params = _clean_params(
                {name: getattr(args, name) for name in SEARCH_FIELDS}
            )

            def fetch_search(cursor: str | None) -> dict[str, Any]:
                return client.search_creatives(
                    {**base_params, "limit": args.limit, "cursor": cursor}
                )

            return _collect_pages(
                fetch_search,
                cursor=args.cursor,
                all_pages=args.all_pages,
                max_pages=args.max_pages,
            )

        if args.creative_command == "get":
            return client.get_creative(args.library_id, args.detail_grant)

        _validate_page_args(args.limit, args.max_pages)

        def fetch_instances(cursor: str | None) -> dict[str, Any]:
            return client.get_instances(
                args.library_id,
                args.detail_grant,
                limit=args.limit,
                cursor=cursor,
            )

        return _collect_pages(
            fetch_instances,
            cursor=args.cursor,
            all_pages=args.all_pages,
            max_pages=args.max_pages,
        )

    if args.command in ("categories", "category"):
        return client.list_categories()

    if args.command == "api":
        return {
            "capabilities": client.capabilities,
            "usage": client.usage,
            "openapi": client.openapi,
        }[args.api_command]()

    raise AdWallError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    configure_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env(args.env_file)
        client = AdWallClient(settings)
        result = execute(args, client)
        if args.jsonl:
            items = _items_for_jsonl(result)
            if items is None:
                raise ConfigError("--jsonl requires a response with an items array")
            emit_jsonl(items)
        else:
            if args.response_meta and args.command != "auth":
                result = {"data": result, "responseMeta": client.last_response_meta}
            emit(result, compact=args.compact)
    except (AdWallError, OSError, ValueError, json.JSONDecodeError) as exc:
        emit(error_payload(exc), compact=getattr(args, "compact", False))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
