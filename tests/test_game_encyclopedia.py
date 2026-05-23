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

    def test_steam_libraryfolders_vdf_discovers_secondary_library(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            steam_root = root / "Steam"
            library = root / "SteamLibrary"
            (steam_root / "steamapps").mkdir(parents=True)
            (library / "steamapps" / "common" / "Cities Skylines II" / "Cities2_Data" / "Content" / "Game").mkdir(parents=True)
            locale = library / "steamapps" / "common" / "Cities Skylines II" / "Cities2_Data" / "Content" / "Game" / "Locale.cok"
            locale.write_bytes(b"locale")
            (library / "steamapps" / "appmanifest_949230.acf").write_text('"AppState" { "buildid" "23061229" }', encoding="utf-8")
            (steam_root / "steamapps" / "libraryfolders.vdf").write_text(
                '"libraryfolders"\n{\n  "0" { "path" "' + str(steam_root).replace("\\", "\\\\") + '" }\n'
                '  "1" { "path" "' + str(library).replace("\\", "\\\\") + '" }\n}\n',
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": "", "CITIES2_LOCALE_COK": ""}, clear=False):
                result = find_locale_cok(EncyclopediaConfig(), steam_roots=[steam_root])

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, locale.resolve())
        self.assertEqual(result.source_kind, "steam")
        self.assertEqual(result.steam_app_id, "949230")
        self.assertEqual(result.steam_build_id, "23061229")

    def test_missing_source_returns_nonfatal_warning_status(self) -> None:
        with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": "", "CITIES2_LOCALE_COK": ""}, clear=False):
            result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])
            payload = source_status_payload(result, cache_status="unavailable", entry_count=0)

        self.assertFalse(payload["available"])
        self.assertEqual(payload["warning"], GAME_ENCYCLOPEDIA_WARNING)
        self.assertEqual(payload["cache_status"], "unavailable")
        self.assertEqual(payload["entry_count"], 0)


from game_encyclopedia import (  # noqa: E402
    cache_dir_default,
    cache_is_fresh,
    current_source_fingerprint,
    load_cached_entries,
    write_cache,
)


class GameEncyclopediaCacheTests(unittest.TestCase):
    def test_cache_hit_requires_matching_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(b"abc")
            discovery = find_locale_cok(EncyclopediaConfig(locale_cok=locale), steam_roots=[])
            fingerprint = current_source_fingerprint(discovery, locale="en-US")
            cache_dir = root / "cache"
            entries = [{"entry_id": "roads", "title": "Roads", "text": "Road text"}]

            write_cache(cache_dir, fingerprint, entries, chunks=entries)

            self.assertTrue(cache_is_fresh(cache_dir, fingerprint))
            loaded = load_cached_entries(cache_dir)
            self.assertEqual(loaded, entries)

            stale = dict(fingerprint)
            stale["locale_cok_size"] = fingerprint["locale_cok_size"] + 1
            self.assertFalse(cache_is_fresh(cache_dir, stale))

    def test_default_cache_dir_is_user_local(self) -> None:
        path = cache_dir_default()
        self.assertIn("game-encyclopedia", str(path))

    def test_cache_is_stale_when_jsonl_is_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(b"abc")
            discovery = find_locale_cok(EncyclopediaConfig(locale_cok=locale), steam_roots=[])
            fingerprint = current_source_fingerprint(discovery, locale="en-US")
            cache_dir = root / "cache"
            entries = [{"entry_id": "roads", "title": "Roads", "text": "Road text"}]
            write_cache(cache_dir, fingerprint, entries, chunks=entries)

            (cache_dir / "entries.jsonl").write_text("{not json}\n", encoding="utf-8")

            self.assertFalse(cache_is_fresh(cache_dir, fingerprint))

    def test_cache_is_stale_when_manifest_counts_do_not_match_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(b"abc")
            discovery = find_locale_cok(EncyclopediaConfig(locale_cok=locale), steam_roots=[])
            fingerprint = current_source_fingerprint(discovery, locale="en-US")
            cache_dir = root / "cache"
            entries = [{"entry_id": "roads", "title": "Roads", "text": "Road text"}]
            write_cache(cache_dir, fingerprint, entries, chunks=entries)

            (cache_dir / "chunks.jsonl").write_text("", encoding="utf-8")

            self.assertFalse(cache_is_fresh(cache_dir, fingerprint))


if __name__ == "__main__":
    unittest.main()
