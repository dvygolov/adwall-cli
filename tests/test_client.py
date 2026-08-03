import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from adwall_cli.client import AdWallClient
from adwall_cli.config import Settings
from adwall_cli.graphql import CURRENT_USER


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    calls = []

    def log_message(self, *args):
        pass

    def _json(self, value):
        raw = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        operation = body.get("operationName")
        authorization = self.headers.get("Authorization")
        Handler.calls.append((operation, authorization, body.get("variables")))
        if operation == "SignIn":
            self._json(
                {
                    "data": {
                        "signIn": {
                            "accessToken": "old-access",
                            "refreshToken": "refresh-1",
                            "user": {"id": "u1", "email": "agent@example.test"},
                        }
                    }
                }
            )
            return
        if operation == "RenewTokens" and authorization == "Bearer refresh-1":
            self._json(
                {
                    "data": {
                        "renewTokens": {
                            "accessToken": "new-access",
                            "refreshToken": "refresh-2",
                        }
                    }
                }
            )
            return
        if operation == "GetCurrentUser" and authorization == "Bearer new-access":
            self._json({"data": {"getCurrentUser": {"id": "u1"}}})
            return
        if operation == "GetCurrentUser":
            self._json(
                {
                    "errors": [
                        {
                            "message": "Token expired",
                            "extensions": {"code": "UNAUTHENTICATED"},
                        }
                    ]
                }
            )
            return
        self._json({"errors": [{"message": "unexpected operation"}]})


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.calls = []

    def _settings(self, session_file):
        url = f"http://127.0.0.1:{self.server.server_port}/graphql"
        return Settings(
            api_url=url,
            stats_api_url=url,
            proxies_api_url=url,
            admin_api_url=url,
            email="agent@example.test",
            password="secret",
            session_file=session_file,
            timeout=3,
            env_file=None,
        )

    def test_login_persists_tokens_without_returning_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_file = Path(tmp) / "session.json"
            client = AdWallClient(self._settings(session_file))
            user = client.login()
            self.assertEqual(user["email"], "agent@example.test")
            stored = json.loads(session_file.read_text(encoding="utf-8"))
            self.assertEqual(stored["access_token"], "old-access")
            self.assertNotIn("password", stored)

    def test_unauthenticated_error_renews_and_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_file = Path(tmp) / "session.json"
            session_file.write_text(
                json.dumps(
                    {"access_token": "old-access", "refresh_token": "refresh-1"}
                ),
                encoding="utf-8",
            )
            client = AdWallClient(self._settings(session_file))
            data = client.request(CURRENT_USER, {}, "GetCurrentUser")
            self.assertEqual(data["getCurrentUser"]["id"], "u1")
            operations = [call[0] for call in Handler.calls]
            self.assertEqual(
                operations, ["GetCurrentUser", "RenewTokens", "GetCurrentUser"]
            )
            stored = json.loads(session_file.read_text(encoding="utf-8"))
            self.assertEqual(stored["access_token"], "new-access")


if __name__ == "__main__":
    unittest.main()
