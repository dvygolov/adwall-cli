import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adwall_cli.config import Settings


class SettingsTests(unittest.TestCase):
    def test_loads_env_and_resolves_session_next_to_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "ADWALL_API_URL=https://example.test/graphql\n"
                "ADWALL_EMAIL=agent@example.test\n"
                "ADWALL_SESSION_FILE=state/session.json\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings.from_env(str(env_file))
            self.assertEqual(settings.api_url, "https://example.test/graphql")
            self.assertEqual(settings.email, "agent@example.test")
            self.assertEqual(settings.timeout, 60)
            self.assertEqual(
                settings.session_file, (Path(tmp) / "state/session.json").resolve()
            )

    def test_real_environment_wins_over_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "ADWALL_EMAIL=file@example.test\n", encoding="utf-8"
            )
            with patch.dict(
                os.environ, {"ADWALL_EMAIL": "real@example.test"}, clear=True
            ):
                settings = Settings.from_env(str(env_file))
            self.assertEqual(settings.email, "real@example.test")


if __name__ == "__main__":
    unittest.main()
