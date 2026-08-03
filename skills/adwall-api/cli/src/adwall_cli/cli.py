from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .client import AdWallClient
from .config import Settings
from .errors import AdWallError, ConfigError
from .graphql import (
    ADD_FAVORITE,
    CREATE_BLACKLIST_RULE,
    CURRENT_USER,
    FIND_APPS,
    FIND_ARCHIVES,
    GET_AD,
    GET_ADS,
    GET_AFFECTED_BLACKLIST,
    GET_BLACKLIST_RULES,
    GET_CATEGORIES,
    GET_COUNTRIES,
    GET_DIRECT_BLACKLIST,
    GET_FAVORITES,
    GET_LANGUAGES,
    INITIALIZE_ARCHIVE,
    REMOVE_ALL_AD_RULES,
    REMOVE_BLACKLIST_RULE,
    REMOVE_FAVORITE,
    RETRY_ARCHIVE,
    TOGGLE_FAVORITE,
)
from .output import configure_utf8_stdout, emit, emit_jsonl, error_payload


MEDIA_FORMATS = ("Carousel", "Image", "None", "Video")
PUBLISHER_PLATFORMS = (
    "AudienceNetwork",
    "Facebook",
    "Instagram",
    "Messenger",
    "Oculus",
    "Threads",
    "WhatsApp",
)
APP_PLATFORMS = ("Android", "IOs")
APP_HOSTINGS = ("AppStore", "GooglePlay")
SPECIAL_CATEGORIES = (
    "CreditAds",
    "EmploymentAds",
    "HousingAds",
    "PoliticalAndIssueAds",
)
BLACKLIST_ATTRIBUTES = ("AppId", "FbPageId", "Hostname", "IpAddress")
APP_SORT_FIELDS = (
    "AppPlatform",
    "AppName",
    "TotalAdsPerPeriod",
    "TotalRelatedMetaPages",
    "FirstAdAppearedAt",
    "LastAdAppearedAt",
)


def _flatten(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(item.strip() for item in value.split(",") if item.strip())
    return list(dict.fromkeys(result))


def _yes_no(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "yes"


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        result = {key: _clean(item) for key, item in value.items()}
        return {
            key: item
            for key, item in result.items()
            if item is not None and item != "" and item != [] and item != {}
        }
    if isinstance(value, list):
        return [_clean(item) for item in value if item is not None and item != ""]
    return value


def _date_period(start: str | None, end: str | None, label: str) -> dict[str, str] | None:
    if bool(start) != bool(end):
        raise ConfigError(f"{label} requires both from and to dates")
    return {"startDate": start, "endDate": end} if start and end else None


def _require_yes(args: argparse.Namespace, action: str) -> None:
    if not getattr(args, "yes", False):
        raise AdWallError(f"{action} requires explicit --yes")


def _add_yes(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--yes", action="store_true", help="Confirm the mutation")


def _add_cursor_args(parser: argparse.ArgumentParser, *, default: int = 10) -> None:
    parser.add_argument("--limit", type=int, default=default, help="Objects per request")
    parser.add_argument("--after", help="Cursor returned by a previous request")
    parser.add_argument("--all-pages", action="store_true")
    parser.add_argument("--max-pages", type=int, default=5)


def _add_search_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", help="Shortcut for --text-body")
    parser.add_argument("--text-body")
    parser.add_argument("--page-name")
    parser.add_argument("--image-text")
    parser.add_argument("--link-text")
    parser.add_argument("--url", dest="target_url")
    parser.add_argument("--country", action="append")
    parser.add_argument("--countries-count", type=int)
    parser.add_argument("--language", action="append")
    parser.add_argument("--format", dest="formats", choices=MEDIA_FORMATS, action="append")
    parser.add_argument(
        "--placement", choices=PUBLISHER_PLATFORMS, action="append"
    )
    parser.add_argument("--created-from", metavar="YYYY-MM-DD")
    parser.add_argument("--created-to", metavar="YYYY-MM-DD")
    parser.add_argument("--delivery-from", metavar="YYYY-MM-DD")
    parser.add_argument("--delivery-to", metavar="YYYY-MM-DD")
    parser.add_argument("--hostname")
    parser.add_argument("--ip-address")
    parser.add_argument("--tld", action="append")
    parser.add_argument("--app-id")
    parser.add_argument("--app-platform", choices=APP_PLATFORMS)
    parser.add_argument("--app-hosting", choices=APP_HOSTINGS)
    parser.add_argument("--meta-page-id")
    parser.add_argument("--lead-form", choices=("yes", "no"))
    parser.add_argument("--cta", action="append", help="GraphQL CallToActionKey")
    parser.add_argument("--category-id", action="append")
    parser.add_argument("--cloaked", choices=("yes", "no"))
    parser.add_argument("--additional-assets", choices=("yes", "no"))
    parser.add_argument(
        "--special-category", choices=SPECIAL_CATEGORIES, action="append"
    )


def _search_filter(args: argparse.Namespace) -> dict[str, Any]:
    text_body = args.text_body or args.query
    value = {
        "textSearch": {
            "targetLinkUrl": args.target_url,
            "metaPageName": args.page_name,
            "creativeLinkText": args.link_text,
            "creativeBody": text_body,
            "textOnImages": args.image_text,
        },
        "shownInCountries": _flatten(args.country),
        "shownInTotalCountries": args.countries_count,
        "languages": _flatten(args.language),
        "mediaDisplayFormats": _flatten(args.formats),
        "creationPeriod": _date_period(
            args.created_from, args.created_to, "Creation period"
        ),
        "deliveryPeriod": _date_period(
            args.delivery_from, args.delivery_to, "Delivery period"
        ),
        "targetLink": {
            "contentInspection": {"isProbablyCloaked": _yes_no(args.cloaked)},
            "topLevelDomainsList": ",".join(_flatten(args.tld)) or None,
            "ipAddress": args.ip_address,
            "hostname": args.hostname,
        },
        "targetApp": {
            "platform": args.app_platform,
            "id": args.app_id,
            "hosting": args.app_hosting,
        },
        "metaPage": {"id": args.meta_page_id},
        "publisherPlatforms": _flatten(args.placement),
        "includesLeadTypeForm": _yes_no(args.lead_form),
        "callToActionTypes": _flatten(args.cta),
        "attachedCategoryIds": _flatten(args.category_id),
        "hasAdditionalAssets": _yes_no(args.additional_assets),
        "specialCategories": _flatten(args.special_category),
    }
    return _clean(value)


def _at_path(data: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any]:
    current: Any = data
    for name in path:
        if not isinstance(current, dict) or not isinstance(current.get(name), dict):
            raise AdWallError(f"Response is missing {'.'.join(path)}")
        current = current[name]
    return current


def _collect_cursor(
    client: AdWallClient,
    *,
    query: str,
    operation: str,
    variables: dict[str, Any],
    path: tuple[str, ...],
    endpoint: str = "api",
    all_pages: bool,
    max_pages: int,
) -> dict[str, Any]:
    if variables.get("first", 1) <= 0:
        raise ConfigError("--limit must be positive")
    if max_pages <= 0:
        raise ConfigError("--max-pages must be positive")
    data = client.request(query, variables, operation, endpoint=endpoint)
    page = _at_path(data, path)
    if not all_pages:
        return data
    edges = list(page.get("edges") or [])
    page_info = dict(page.get("pageInfo") or {})
    pages = 1
    while page_info.get("hasNextPage") and pages < max_pages:
        cursor = page_info.get("endCursor")
        if not cursor:
            break
        variables = {**variables, "after": cursor}
        next_data = client.request(query, variables, operation, endpoint=endpoint)
        next_page = _at_path(next_data, path)
        edges.extend(next_page.get("edges") or [])
        page_info = dict(next_page.get("pageInfo") or {})
        pages += 1
    page["edges"] = edges
    page["pageInfo"] = page_info
    page["pagesFetched"] = pages
    return data


def _find_edges(value: Any) -> list[Any] | None:
    if isinstance(value, dict):
        if isinstance(value.get("edges"), list):
            return [edge.get("node", edge) if isinstance(edge, dict) else edge for edge in value["edges"]]
        for item in value.values():
            found = _find_edges(item)
            if found is not None:
                return found
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adwall", description="Agent-first CLI for AdWall's web GraphQL APIs."
    )
    parser.add_argument("--env-file", help="Path to .env (default: ./.env)")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    parser.add_argument("--jsonl", action="store_true", help="Emit paginated objects as JSONL")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    auth = commands.add_parser("auth")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)
    login = auth_sub.add_parser("login")
    login.add_argument("--email")
    auth_sub.add_parser("status")
    auth_sub.add_parser("logout")

    creatives = commands.add_parser("creatives", aliases=["creative"])
    creative_sub = creatives.add_subparsers(dest="creative_command", required=True)
    search = creative_sub.add_parser("search")
    _add_cursor_args(search)
    _add_search_filters(search)
    get_ad = creative_sub.add_parser("get")
    get_ad.add_argument("id")

    dictionaries = commands.add_parser("dictionaries", aliases=["dictionary"])
    dictionary_sub = dictionaries.add_subparsers(dest="dictionary_command", required=True)
    dictionary_sub.add_parser("categories")
    for name in ("countries", "languages"):
        item = dictionary_sub.add_parser(name)
        _add_cursor_args(item, default=100)

    favorites = commands.add_parser("favorites", aliases=["favorite"])
    favorite_sub = favorites.add_subparsers(dest="favorite_command", required=True)
    favorite_list = favorite_sub.add_parser("list")
    _add_cursor_args(favorite_list)
    _add_search_filters(favorite_list)
    for name in ("add", "remove", "toggle"):
        item = favorite_sub.add_parser(name)
        item.add_argument("ad_id")
        _add_yes(item)

    blacklist = commands.add_parser("blacklist")
    blacklist_sub = blacklist.add_subparsers(dest="blacklist_command", required=True)
    rules = blacklist_sub.add_parser("rules")
    rules.add_argument("--page", type=int, default=1)
    rules.add_argument("--page-size", type=int, default=25)
    rules.add_argument("--attribute", choices=BLACKLIST_ATTRIBUTES)
    rules.add_argument("--value")
    direct = blacklist_sub.add_parser("direct")
    _add_cursor_args(direct)
    affected = blacklist_sub.add_parser("affected")
    affected.add_argument("attribute", choices=BLACKLIST_ATTRIBUTES)
    affected.add_argument("value")
    affected.add_argument("--include-direct", action="store_true")
    _add_cursor_args(affected)
    add_rule = blacklist_sub.add_parser("add-rule")
    add_rule.add_argument("ad_id")
    add_rule.add_argument("attribute", choices=BLACKLIST_ATTRIBUTES)
    _add_yes(add_rule)
    remove_rule = blacklist_sub.add_parser("remove-rule")
    remove_rule.add_argument("attribute", choices=BLACKLIST_ATTRIBUTES)
    remove_rule.add_argument("value")
    _add_yes(remove_rule)
    clear_ad = blacklist_sub.add_parser("clear-ad")
    clear_ad.add_argument("ad_id")
    _add_yes(clear_ad)

    apps = commands.add_parser("apps")
    apps_sub = apps.add_subparsers(dest="apps_command", required=True)
    apps_search = apps_sub.add_parser("search")
    apps_search.add_argument("--name")
    apps_search.add_argument("--platform", choices=APP_PLATFORMS)
    apps_search.add_argument("--status", choices=("alive", "banned"))
    apps_search.add_argument("--from", dest="period_from", metavar="YYYY-MM-DD")
    apps_search.add_argument("--to", dest="period_to", metavar="YYYY-MM-DD")
    apps_search.add_argument("--page", type=int, default=1)
    apps_search.add_argument("--page-size", type=int, default=25)
    apps_search.add_argument("--sort", choices=APP_SORT_FIELDS)
    apps_search.add_argument("--direction", choices=("asc", "desc"))

    archives = commands.add_parser("archives", aliases=["archive"])
    archive_sub = archives.add_subparsers(dest="archive_command", required=True)
    archive_list = archive_sub.add_parser("list")
    archive_list.add_argument("--page", type=int, default=1)
    archive_list.add_argument("--page-size", type=int, default=18)
    archive_create = archive_sub.add_parser("create")
    archive_create.add_argument("url")
    archive_create.add_argument("--country")
    _add_yes(archive_create)
    archive_retry = archive_sub.add_parser("retry")
    archive_retry.add_argument("archive_id")
    _add_yes(archive_retry)

    raw = commands.add_parser("raw")
    raw.add_argument("endpoint", choices=("api", "stats", "proxies", "admin"))
    raw.add_argument("query_file", type=Path)
    raw.add_argument("--variables", help="JSON object")
    raw.add_argument("--variables-file", type=Path)
    raw.add_argument("--operation-name")
    _add_yes(raw)
    return parser


def execute(args: argparse.Namespace, client: AdWallClient) -> Any:
    if args.command == "auth":
        if args.auth_command == "login":
            email = args.email or client.settings.email
            if not email:
                email = input("AdWall email: ").strip()
            password = client.settings.password
            if not password:
                password = getpass.getpass("AdWall password: ")
            user = client.login(email, password)
            return {
                "success": True,
                "authenticated": True,
                "user": user,
                "session_file": str(client.settings.session_file),
            }
        if args.auth_command == "status":
            data = client.request(CURRENT_USER, {}, "GetCurrentUser")
            return {
                "success": True,
                "authenticated": True,
                "user": data.get("getCurrentUser"),
                "session_file": str(client.settings.session_file),
            }
        client.clear_session()
        return {"success": True, "authenticated": False}

    if args.command in ("creatives", "creative"):
        if args.creative_command == "get":
            return client.request(GET_AD, {"id": args.id}, "GetAd")
        variables = {
            "after": args.after,
            "first": args.limit,
            "filter": _search_filter(args),
            "dataset": "Unique",
        }
        return _collect_cursor(
            client,
            query=GET_ADS,
            operation="GetAds",
            variables=variables,
            path=("getAds",),
            all_pages=args.all_pages,
            max_pages=args.max_pages,
        )

    if args.command in ("dictionaries", "dictionary"):
        if args.dictionary_command == "categories":
            return client.request(GET_CATEGORIES, {}, "GetAdsCategories")
        is_countries = args.dictionary_command == "countries"
        query = GET_COUNTRIES if is_countries else GET_LANGUAGES
        operation = "GetCountriesDictionaries" if is_countries else "GetCountriesLanguages"
        name = "countries" if is_countries else "languages"
        return _collect_cursor(
            client,
            query=query,
            operation=operation,
            variables={"after": args.after, "first": args.limit},
            path=("getDictionaries", name),
            all_pages=args.all_pages,
            max_pages=args.max_pages,
        )

    if args.command in ("favorites", "favorite"):
        if args.favorite_command == "list":
            return _collect_cursor(
                client,
                query=GET_FAVORITES,
                operation="GetFavorites",
                variables={
                    "after": args.after,
                    "first": args.limit,
                    "filter": _search_filter(args),
                },
                path=("getFavorites",),
                all_pages=args.all_pages,
                max_pages=args.max_pages,
            )
        _require_yes(args, f"Favorite {args.favorite_command}")
        query, operation = {
            "add": (ADD_FAVORITE, "AddAdToFavorites"),
            "remove": (REMOVE_FAVORITE, "RemoveAdFromFavorites"),
            "toggle": (TOGGLE_FAVORITE, "ToggleAdInFavorites"),
        }[args.favorite_command]
        return client.request(query, {"adId": args.ad_id}, operation)

    if args.command == "blacklist":
        if args.blacklist_command == "rules":
            return client.request(
                GET_BLACKLIST_RULES,
                {
                    "pagination": {"pageNumber": args.page, "pageSize": args.page_size},
                    "filter": _clean(
                        {
                            "blacklistAttribute": args.attribute,
                            "searchAttributeValue": args.value,
                        }
                    ),
                },
                "GetBlacklistRules",
            )
        if args.blacklist_command == "direct":
            return _collect_cursor(
                client,
                query=GET_DIRECT_BLACKLIST,
                operation="GetDirectlyBlacklistedAds",
                variables={"after": args.after, "first": args.limit},
                path=("getDirectlyBlacklistedAds",),
                all_pages=args.all_pages,
                max_pages=args.max_pages,
            )
        if args.blacklist_command == "affected":
            return _collect_cursor(
                client,
                query=GET_AFFECTED_BLACKLIST,
                operation="GetBlacklistedAds",
                variables={
                    "after": args.after,
                    "first": args.limit,
                    "filter": {
                        "byBlacklistRule": {
                            "blacklistAttribute": args.attribute,
                            "attributeValue": args.value,
                        },
                        "excludeDirectlyBlacklisted": not args.include_direct,
                    },
                },
                path=("getBlacklistedAds",),
                all_pages=args.all_pages,
                max_pages=args.max_pages,
            )
        _require_yes(args, f"Blacklist {args.blacklist_command}")
        if args.blacklist_command == "add-rule":
            return client.request(
                CREATE_BLACKLIST_RULE,
                {"adId": args.ad_id, "blacklistAttribute": args.attribute},
                "CreateBlacklistRuleBasedOnAttribute",
            )
        if args.blacklist_command == "remove-rule":
            return client.request(
                REMOVE_BLACKLIST_RULE,
                {"blacklistAttribute": args.attribute, "attributeValue": args.value},
                "RemoveBlacklistRule",
            )
        return client.request(
            REMOVE_ALL_AD_RULES,
            {"adId": args.ad_id},
            "RemoveAllBlacklistRulesThatAffectAd",
        )

    if args.command == "apps":
        period = _date_period(args.period_from, args.period_to, "App period")
        status = None if args.status is None else args.status == "banned"
        variables = {
            "filter": _clean(
                {
                    "app": {"name": args.name, "platform": args.platform, "is404": status},
                    "period": (
                        {"start": period["startDate"], "end": period["endDate"]}
                        if period
                        else None
                    ),
                }
            ),
            "pagination": {"pageNumber": args.page, "pageSize": args.page_size},
            "sorting": _clean({"field": args.sort, "direction": args.direction}),
        }
        return client.request(
            FIND_APPS, variables, "FindAppCoverageReports", endpoint="stats"
        )

    if args.command in ("archives", "archive"):
        if args.archive_command == "list":
            return client.request(
                FIND_ARCHIVES,
                {"pagination": {"pageNumber": args.page, "pageSize": args.page_size}},
                "FindMyWebpageArchivals",
                endpoint="proxies",
            )
        _require_yes(args, f"Archive {args.archive_command}")
        if args.archive_command == "create":
            return client.request(
                INITIALIZE_ARCHIVE,
                {"url": args.url, "countryCode": args.country},
                "InitializeWebpageArchival",
                endpoint="proxies",
            )
        return client.request(
            RETRY_ARCHIVE,
            {"webpageArchivalId": args.archive_id},
            "RetryFailedWebpageArchival",
            endpoint="proxies",
        )

    if args.command == "raw":
        query = args.query_file.read_text(encoding="utf-8")
        match = re.search(r"\b(query|mutation)\s+([A-Za-z_][A-Za-z0-9_]*)", query)
        operation = args.operation_name or (match.group(2) if match else None)
        if not operation:
            raise ConfigError("Set --operation-name for an anonymous GraphQL document")
        if re.search(r"\bmutation\b", query):
            _require_yes(args, "Raw GraphQL mutation")
        if args.variables and args.variables_file:
            raise ConfigError("Use either --variables or --variables-file")
        raw_variables = (
            args.variables_file.read_text(encoding="utf-8")
            if args.variables_file
            else args.variables or "{}"
        )
        variables = json.loads(raw_variables)
        if not isinstance(variables, dict):
            raise ConfigError("GraphQL variables must be a JSON object")
        return client.request(
            query, variables, operation, endpoint=args.endpoint
        )
    raise AdWallError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    configure_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env(args.env_file)
        result = execute(args, AdWallClient(settings))
        if args.jsonl:
            items = _find_edges(result)
            if items is None:
                raise ConfigError("--jsonl is available only for cursor-paginated results")
            emit_jsonl(items)
        else:
            emit(result, compact=args.compact)
    except (AdWallError, OSError, ValueError, json.JSONDecodeError) as exc:
        emit(error_payload(exc), compact=getattr(args, "compact", False))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
