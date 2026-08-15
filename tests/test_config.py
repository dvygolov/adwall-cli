import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adwall_cli.config import Settings
from adwall_cli.errors import ConfigError


class SettingsTests(unittest.TestCase):
    def test_official_api_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()

        self.assertIsNone(settings.api_key)
        self.assertEqual(settings.base_url, "https://adwall.io/api")
        self.assertEqual(settings.timeout, 60)
        self.assertIsNone(settings.env_file)

    def test_loads_api_key_base_url_and_timeout_from_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "ADWALL_API_KEY='agent-secret'\n"
                "ADWALL_BASE_URL=https://example.test/custom-api\n"
                "ADWALL_TIMEOUT=12.5\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings.from_env(str(env_file))

        self.assertEqual(settings.api_key, "agent-secret")
        self.assertEqual(settings.base_url, "https://example.test/custom-api")
        self.assertEqual(settings.timeout, 12.5)
        self.assertEqual(settings.env_file, env_file.resolve())

    def test_real_environment_wins_over_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "ADWALL_API_KEY=file-key\n"
                "ADWALL_BASE_URL=https://file.example/api\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "ADWALL_API_KEY": "environment-key",
                    "ADWALL_BASE_URL": "https://environment.example/api",
                },
                clear=True,
            ):
                settings = Settings.from_env(str(env_file))

        self.assertEqual(settings.api_key, "environment-key")
        self.assertEqual(settings.base_url, "https://environment.example/api")

    def test_rejects_non_numeric_or_non_positive_timeout(self):
        for value in ("forever", "0", "-1"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"ADWALL_TIMEOUT": value}, clear=True
            ):
                with self.assertRaises(ConfigError):
                    Settings.from_env()


if __name__ == "__main__":
    unittest.main()
