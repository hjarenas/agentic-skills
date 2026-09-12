from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


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


class OversizedCheckTests(unittest.TestCase):
    """End to end through main(): an emphasised limit is honoured, and a page of
    exactly the limit (newline-terminated, as editors write it) is not over it."""

    def lint(self, page_lines: int) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "docs" / "archi"
            (root / "pages").mkdir(parents=True)
            (root / "SCHEMA.md").write_text("A page over **20 lines** must be split.\n", encoding="utf-8")
            (root / "index.md").write_text("- [[a]] — a\n- [[b]] — b\n", encoding="utf-8")
            head = "---\ntitle: A\nstatus: current\nupdated: 2026-01-01\nlinks: [b]\n---\n[[b]]\n"
            body = "".join(f"line {i}\n" for i in range(page_lines - head.count("\n")))
            (root / "pages" / "a.md").write_text(head + body, encoding="utf-8")
            (root / "pages" / "b.md").write_text(
                "---\ntitle: B\nstatus: current\nupdated: 2026-01-01\nlinks: [a]\n---\n[[a]]\n", encoding="utf-8"
            )
            out = StringIO()
            with patch("sys.argv", ["wiki_lint.py", "--root", str(root), "--json"]), redirect_stdout(out):
                wiki_lint.main()
            return [f for f in json.loads(out.getvalue())["findings"] if f["check"] == "oversized"]

    def test_page_at_the_limit_is_not_oversized(self) -> None:
        self.assertEqual(self.lint(20), [])

    def test_page_past_the_emphasised_limit_is_oversized(self) -> None:
        findings = self.lint(21)
        self.assertEqual([f["page"] for f in findings], ["a"])
        self.assertIn("21 lines exceeds the 20-line limit", findings[0]["detail"])


if __name__ == "__main__":
    unittest.main()
