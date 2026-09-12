from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "wiki_lint.py"
SPEC = importlib.util.spec_from_file_location("wiki_lint", SCRIPT)
assert SPEC and SPEC.loader
wiki_lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wiki_lint)


class SchemaSizeLimitTests(unittest.TestCase):
    def test_plain_number(self) -> None:
        self.assertEqual(wiki_lint.schema_size_limit("A page over 250 lines must be split.", 400), 250)

    def test_bold_number_and_unit(self) -> None:
        # The phrasing wiki-init's template invites: `**350 lines**`.
        self.assertEqual(wiki_lint.schema_size_limit("A page over **350 lines** must be split.", 400), 350)

    def test_bold_number_only(self) -> None:
        self.assertEqual(wiki_lint.schema_size_limit("A page over **350** lines must be split.", 400), 350)

    def test_italic_number(self) -> None:
        self.assertEqual(wiki_lint.schema_size_limit("A page over _300_ lines must be split.", 400), 300)

    def test_case_insensitive(self) -> None:
        self.assertEqual(wiki_lint.schema_size_limit("## Size limit\n\nPage over 200 Lines: split.", 400), 200)

    def test_falls_back_to_default(self) -> None:
        self.assertEqual(wiki_lint.schema_size_limit("No size rule here.", 400), 400)


if __name__ == "__main__":
    unittest.main()
