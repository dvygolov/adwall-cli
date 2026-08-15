import unittest
from types import SimpleNamespace

from adwall_cli.cli import build_parser, execute


class FakeClient:
    def __init__(self, api_key="test-api-key"):
        self.calls = []
        self.settings = SimpleNamespace(
            api_key=api_key,
            base_url="https://adwall.io/api",
            env_file=None,
        )

    def search_creatives(self, filters):
        self.calls.append(("search_creatives", filters))
        return {"items": []}

    def get_creative(self, library_id, detail_grant=None):
        self.calls.append(("get_creative", library_id, detail_grant))
        return {"library_id": library_id}

    def get_instances(self, library_id, detail_grant, *, limit=None, cursor=None):
        self.calls.append(
            ("get_instances", library_id, detail_grant, limit, cursor)
        )
        return {"items": []}

    def list_categories(self):
        self.calls.append(("list_categories",))
        return {"items": []}

    def capabilities(self):
        self.calls.append(("capabilities",))
        return {"version": "1.1.0"}

    def usage(self):
        self.calls.append(("usage",))
        return {"used": 0}

    def openapi(self):
        self.calls.append(("openapi",))
        return {"openapi": "3.1.0"}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.client = FakeClient()

    def parse(self, *argv):
        return self.parser.parse_args(list(argv))

    def test_auth_status_is_local_and_does_not_reveal_key(self):
        result = execute(self.parse("auth", "status"), self.client)

        self.assertTrue(result["configured"])
        self.assertEqual(self.client.calls, [])
        self.assertNotIn("test-api-key", repr(result))

        missing = FakeClient(api_key=None)
        self.assertFalse(execute(self.parse("auth", "status"), missing)["configured"])
        self.assertEqual(missing.calls, [])

    def test_search_maps_all_official_filters_without_graphql_translation(self):
        args = self.parse(
            "creatives",
            "search",
            "--q",
            "casino",
            "--advertiser",
            "Lucky Page",
            "--target-url",
            "https://example.test/offer?a=1",
            "--link-text",
            "Learn more",
            "--image-text",
            "Bonus",
            "--geo",
            "CZ,GB",
            "--language",
            "en",
            "--platform",
            "facebook",
            "--format",
            "video",
            "--cta",
            "LEARN_MORE",
            "--category-id",
            "category-1",
            "--published-from",
            "2026-07-01",
            "--published-to",
            "2026-08-01",
            "--running-from",
            "2026-07-02",
            "--running-to",
            "2026-08-02",
            "--domain",
            "example.test",
            "--tld",
            "test",
            "--app",
            "com.example.app",
            "--app-platform",
            "android",
            "--special-category",
            "credit",
            "--countries-count",
            "2",
            "--sort",
            "published_at",
            "--order",
            "desc",
            "--limit",
            "25",
            "--cursor",
            "next-page",
        )

        execute(args, self.client)

        self.assertEqual(
            self.client.calls,
            [
                (
                    "search_creatives",
                    {
                        "q": "casino",
                        "advertiser": "Lucky Page",
                        "target_url": "https://example.test/offer?a=1",
                        "link_text": "Learn more",
                        "image_text": "Bonus",
                        "geo": "CZ,GB",
                        "language": "en",
                        "platform": "facebook",
                        "format": "video",
                        "cta": "LEARN_MORE",
                        "category_id": "category-1",
                        "published_from": "2026-07-01",
                        "published_to": "2026-08-01",
                        "running_from": "2026-07-02",
                        "running_to": "2026-08-02",
                        "domain": "example.test",
                        "tld": "test",
                        "app": "com.example.app",
                        "app_platform": "android",
                        "special_category": "credit",
                        "countries_count": 2,
                        "sort": "published_at",
                        "order": "desc",
                        "limit": 25,
                        "cursor": "next-page",
                    },
                )
            ],
        )

    def test_search_does_not_add_unspecified_official_filters(self):
        execute(self.parse("creatives", "search", "--q", "casino"), self.client)

        self.assertEqual(
            self.client.calls,
            [
                (
                    "search_creatives",
                    {"q": "casino", "limit": 10, "cursor": None},
                )
            ],
        )

    def test_get_uses_library_id_and_optional_detail_grant(self):
        execute(
            self.parse("creatives", "get", "123456", "--detail-grant", "grant-1"),
            self.client,
        )
        self.assertEqual(self.client.calls, [("get_creative", "123456", "grant-1")])

        client = FakeClient()
        execute(self.parse("creatives", "get", "654321"), client)
        self.assertEqual(client.calls, [("get_creative", "654321", None)])

    def test_instances_requires_detail_grant_and_maps_pagination(self):
        with self.assertRaises(SystemExit):
            self.parse("creatives", "instances", "123456")

        execute(
            self.parse(
                "creatives",
                "instances",
                "123456",
                "--detail-grant",
                "grant-2",
                "--limit",
                "20",
                "--cursor",
                "cursor-2",
            ),
            self.client,
        )
        self.assertEqual(
            self.client.calls,
            [("get_instances", "123456", "grant-2", 20, "cursor-2")],
        )

    def test_categories_and_api_commands_call_typed_methods(self):
        cases = (
            (("categories", "list"), ("list_categories",)),
            (("api", "capabilities"), ("capabilities",)),
            (("api", "usage"), ("usage",)),
            (("api", "openapi"), ("openapi",)),
        )
        for argv, expected_call in cases:
            with self.subTest(argv=argv):
                client = FakeClient()
                execute(self.parse(*argv), client)
                self.assertEqual(client.calls, [expected_call])

    def test_legacy_graphql_and_mutation_commands_are_removed(self):
        for argv in (
            ("auth", "login"),
            ("favorites", "list"),
            ("blacklist", "rules"),
            ("archives", "list"),
            ("raw", "api", "query.graphql"),
        ):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.parse(*argv)


if __name__ == "__main__":
    unittest.main()
