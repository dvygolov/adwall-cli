import io
import json
import sys
import unittest
from unittest.mock import patch

from adwall_cli.output import configure_utf8_stdout, emit


class OutputTests(unittest.TestCase):
    def test_reconfigures_legacy_windows_stream_for_unicode_json(self):
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="cp1251")

        with patch.object(sys, "stdout", stream):
            configure_utf8_stdout()
            emit({"text": "🎁"})
            stream.flush()

        payload = json.loads(buffer.getvalue().decode("utf-8"))
        self.assertEqual(payload, {"text": "🎁"})


if __name__ == "__main__":
    unittest.main()
