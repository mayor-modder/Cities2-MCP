from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from game_encyclopedia import (  # noqa: E402
    GAME_ENCYCLOPEDIA_WARNING,
    EncyclopediaConfig,
    find_locale_cok,
    source_status_payload,
)


class GameEncyclopediaDiscoveryTests(unittest.TestCase):
    def test_locale_cok_cli_path_has_highest_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            direct = root / "direct" / "Locale.cok"
            env_direct = root / "env" / "Locale.cok"
            direct.parent.mkdir()
            env_direct.parent.mkdir()
            direct.write_bytes(b"direct")
            env_direct.write_bytes(b"env")

            with mock.patch.dict(os.environ, {"CITIES2_LOCALE_COK": str(env_direct)}, clear=False):
                result = find_locale_cok(
                    EncyclopediaConfig(locale_cok=direct),
                    steam_roots=[],
                )

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, direct)
        self.assertEqual(result.source_kind, "explicit_locale_cok")

    def test_direct_locale_cok_outside_game_layout_has_no_game_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            direct = Path(td) / "Locale.cok"
            direct.write_bytes(b"direct")

            result = find_locale_cok(
                EncyclopediaConfig(locale_cok=direct),
                steam_roots=[],
            )
            payload = source_status_payload(result, cache_status="unavailable", entry_count=0)

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, direct)
        self.assertIsNone(result.game_dir)
        self.assertEqual(payload["game_dir"], "")

    def test_game_dir_env_resolves_locale_cok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            game_dir = Path(td) / "Cities Skylines II"
            locale = game_dir / "Cities2_Data" / "Content" / "Game" / "Locale.cok"
            locale.parent.mkdir(parents=True)
            locale.write_bytes(b"game")

            with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": str(game_dir), "CITIES2_LOCALE_COK": ""}, clear=False):
                result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, locale)
        self.assertEqual(result.source_kind, "env_game_dir")

    def test_missing_source_returns_nonfatal_warning_status(self) -> None:
        with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": "", "CITIES2_LOCALE_COK": ""}, clear=False):
            result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])
            payload = source_status_payload(result, cache_status="unavailable", entry_count=0)

        self.assertFalse(payload["available"])
        self.assertEqual(payload["warning"], GAME_ENCYCLOPEDIA_WARNING)
        self.assertEqual(payload["cache_status"], "unavailable")
        self.assertEqual(payload["entry_count"], 0)


if __name__ == "__main__":
    unittest.main()
