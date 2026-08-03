import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from adwall_cli.cli import build_parser, execute
from adwall_cli.errors import AdWallError


class FakeClient:
    def __init__(self):
        self.calls = []
        self.settings = SimpleNamespace(
            password="secret", session_file=Path("session.json")
        )

    def request(self, query, variables, operation_name, **kwargs):
        self.calls.append((operation_name, variables, kwargs))
        if operation_name == "GetAds":
            return {
                "getAds": {
                    "edges": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        return {operation_name: True}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.client = FakeClient()

    def test_search_maps_typed_filters(self):
        args = self.parser.parse_args(
            [
                "creatives",
                "search",
                "--query",
                "casino",
                "--page-name",
                "Lucky Page",
                "--country",
                "CZ,GB",
                "--format",
                "Video",
                "--placement",
                "Facebook",
                "--delivery-from",
                "2026-07-01",
                "--delivery-to",
                "2026-08-01",
                "--hostname",
                "example.com",
                "--app-platform",
                "Android",
                "--lead-form",
                "no",
                "--cloaked",
                "yes",
                "--category-id",
                "category-1",
            ]
        )
        execute(args, self.client)
        operation, variables, _ = self.client.calls[0]
        self.assertEqual(operation, "GetAds")
        search_filter = variables["filter"]
        self.assertEqual(search_filter["textSearch"]["creativeBody"], "casino")
        self.assertEqual(search_filter["textSearch"]["metaPageName"], "Lucky Page")
        self.assertEqual(search_filter["shownInCountries"], ["CZ", "GB"])
        self.assertEqual(search_filter["mediaDisplayFormats"], ["Video"])
        self.assertEqual(search_filter["publisherPlatforms"], ["Facebook"])
        self.assertEqual(
            search_filter["deliveryPeriod"],
            {"startDate": "2026-07-01", "endDate": "2026-08-01"},
        )
        self.assertEqual(search_filter["targetApp"]["platform"], "Android")
        self.assertFalse(search_filter["includesLeadTypeForm"])
        self.assertTrue(
            search_filter["targetLink"]["contentInspection"]["isProbablyCloaked"]
        )

    def test_favorite_mutation_requires_yes(self):
        args = self.parser.parse_args(["favorites", "add", "ad-id"])
        with self.assertRaises(AdWallError):
            execute(args, self.client)

    def test_raw_query_uses_selected_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            query_file = Path(tmp) / "query.graphql"
            query_file.write_text("query Ping { ping }", encoding="utf-8")
            args = self.parser.parse_args(["raw", "stats", str(query_file)])
            execute(args, self.client)
        operation, variables, kwargs = self.client.calls[0]
        self.assertEqual(operation, "Ping")
        self.assertEqual(variables, {})
        self.assertEqual(kwargs["endpoint"], "stats")

    def test_archive_list_matches_first_party_variables(self):
        args = self.parser.parse_args(["archives", "list", "--page-size", "1"])
        execute(args, self.client)
        operation, variables, kwargs = self.client.calls[0]
        self.assertEqual(operation, "FindMyWebpageArchivals")
        self.assertEqual(
            variables, {"pagination": {"pageNumber": 1, "pageSize": 1}}
        )
        self.assertEqual(kwargs["endpoint"], "proxies")


if __name__ == "__main__":
    unittest.main()
