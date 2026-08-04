from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "codex-run.py"
SPEC = importlib.util.spec_from_file_location("codex_run", SCRIPT)
assert SPEC and SPEC.loader
codex_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codex_run)


class FindCompanionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.config = Path(self.tempdir.name)
        self.cache = self.config / "plugins" / "cache"
        self.cache.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def companion(self, relative: str, mtime: int = 1) -> Path:
        path = self.cache / relative / "codex-companion.mjs"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        os.utime(path, (mtime, mtime))
        return path

    def discover(self) -> Path:
        with patch.dict(
            os.environ,
            {"CLAUDE_CONFIG_DIR": str(self.config)},
            clear=False,
        ), patch.dict(os.environ, {"CODEX_COMPANION": ""}, clear=False):
            return codex_run.find_companion()

    def test_discovers_current_marketplace_plugin_version_layout(self) -> None:
        expected = self.companion("openai-codex/codex/1.0.6/scripts")
        self.assertEqual(self.discover(), expected)

    def test_uses_newest_current_installation(self) -> None:
        self.companion("openai-codex/codex/1.0.5/scripts", mtime=10)
        expected = self.companion("openai-codex/codex/1.0.6/scripts", mtime=20)
        self.assertEqual(self.discover(), expected)

    def test_current_layout_wins_over_newer_legacy_cache(self) -> None:
        expected = self.companion("openai-codex/codex/1.0.6/scripts", mtime=10)
        self.companion("legacy/plugins/codex/scripts", mtime=20)
        self.assertEqual(self.discover(), expected)

    def test_supports_both_legacy_layouts(self) -> None:
        self.companion("legacy/plugins/codex/scripts", mtime=10)
        expected = self.companion("market/version/plugins/codex/scripts", mtime=20)
        self.assertEqual(self.discover(), expected)

    def test_valid_override_wins(self) -> None:
        expected = self.config / "custom-companion.mjs"
        expected.touch()
        with patch.dict(os.environ, {"CODEX_COMPANION": str(expected)}):
            self.assertEqual(codex_run.find_companion(), expected)

    def test_invalid_override_fails_without_fallback(self) -> None:
        self.companion("openai-codex/codex/1.0.6/scripts")
        with patch.dict(os.environ, {"CODEX_COMPANION": "/missing/companion"}), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                codex_run.find_companion()

    def test_missing_installation_reports_error(self) -> None:
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.discover()


if __name__ == "__main__":
    unittest.main()
