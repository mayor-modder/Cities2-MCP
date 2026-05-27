from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

from cities2_mcp.game_encyclopedia import (
    GAME_ENCYCLOPEDIA_WARNING,
    EncyclopediaConfig,
    _VDF_PATH_RE,
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

    def test_vdf_path_regex_does_not_ambiguously_match_backslashes(self) -> None:
        self.assertIn(r'[^"\\]', _VDF_PATH_RE.pattern)

    def test_missing_source_returns_nonfatal_warning_status(self) -> None:
        with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": "", "CITIES2_LOCALE_COK": ""}, clear=False):
            result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])
            payload = source_status_payload(result, cache_status="unavailable", entry_count=0)

        self.assertFalse(payload["available"])
        self.assertEqual(payload["warning"], GAME_ENCYCLOPEDIA_WARNING)
        self.assertEqual(payload["cache_status"], "unavailable")
        self.assertEqual(payload["entry_count"], 0)


from cities2_mcp.game_encyclopedia import (
    cache_dir_default,
    cache_is_fresh,
    current_source_fingerprint,
    entries_to_chunks,
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
            entries = [
                {
                    "entry_id": "roads",
                    "source": "game_encyclopedia",
                    "source_key": "Glossary.SECTION_CONTENT[Roads]",
                    "title": "Roads",
                    "tab": "Roads",
                    "category": "Basics",
                    "raw_content": "Road text",
                    "text": "Road text",
                    "locale": "en-US",
                    "metadata": {},
                }
            ]

            write_cache(cache_dir, fingerprint, entries, chunks=entries_to_chunks(entries))

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


from cities2_mcp.game_encyclopedia import (
    clean_markup_text,
    extract_glossary_records,
    records_to_entries,
)


def encode_varint(value: int) -> bytes:
    parts = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            parts.append(byte | 0x80)
        else:
            parts.append(byte)
            break
    return bytes(parts)


def synthetic_locale_blob(records: dict[str, str]) -> bytes:
    blob = bytearray(b"synthetic-header")
    for key, value in records.items():
        key_bytes = key.encode("utf-8")
        value_bytes = value.encode("utf-8")
        blob.extend(encode_varint(len(key_bytes)))
        blob.extend(key_bytes)
        blob.extend(encode_varint(len(value_bytes)))
        blob.extend(value_bytes)
    return bytes(blob)


class GameEncyclopediaParserTests(unittest.TestCase):
    def test_extracts_glossary_records_from_synthetic_locale_blob(self) -> None:
        blob = synthetic_locale_blob(
            {
                "Glossary.TAB[Roads]": "Roads",
                "Glossary.CATEGORY[RoadBasics]": "Road Basics",
                "Glossary.SECTION_TITLE[Roads.RoadBasics.Roads]": "Roads",
                "Glossary.SECTION_CONTENT[Roads.RoadBasics.Roads]": "**Roads** connect zones.\r\n<image:Media/Game/Glossary/Roads.png>",
            }
        )

        records = extract_glossary_records(blob)
        entries = records_to_entries(records, locale="en-US", source_metadata={"steam_build_id": "23061229"})

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["entry_id"], "roads.roadbasics.roads")
        self.assertEqual(entries[0]["tab"], "Roads")
        self.assertEqual(entries[0]["category"], "Road Basics")
        self.assertEqual(entries[0]["title"], "Roads")
        self.assertIn("Roads connect zones.", entries[0]["text"])
        self.assertIn("<image:", entries[0]["raw_content"])
        self.assertEqual(entries[0]["source"], "game_encyclopedia")

    def test_content_section_id_can_contain_title(self) -> None:
        records = synthetic_locale_blob(
            {
                "Glossary.TAB[Roads]": "Roads",
                "Glossary.CATEGORY[RoadBasics]": "Road Basics",
                "Glossary.SECTION_TITLE[Roads.RoadBasics.TITLECase]": "Title Case",
                "Glossary.SECTION_CONTENT[Roads.RoadBasics.TITLECase]": "Content survives.",
            }
        )

        entries = records_to_entries(
            extract_glossary_records(records),
            locale="en-US",
            source_metadata={},
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["entry_id"], "roads.roadbasics.titlecase")
        self.assertEqual(entries[0]["title"], "Title Case")
        self.assertEqual(entries[0]["text"], "Content survives.")

    def test_clean_markup_text_removes_retrieval_noise(self) -> None:
        cleaned = clean_markup_text(
            "**Roads**\r\n<image:Media/Game/Glossary/Roads.png>\r\n"
            "Press <inputAction:Tool.Select> near <icon:Roads>."
        )

        self.assertEqual(cleaned, "Roads\nPress Tool.Select near Roads.")


from cities2_mcp.game_encyclopedia import GameEncyclopediaSource


class GameEncyclopediaSourceTests(unittest.TestCase):
    def test_source_reads_requested_locale_member_from_cok_archive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            en_blob = synthetic_locale_blob(
                {
                    "Glossary.TAB[OfficeZones]": "Office Zones",
                    "Glossary.SECTION_TITLE[OfficeZones]": "Office Zones",
                    "Glossary.SECTION_CONTENT[OfficeZones]": "Office zones need educated workers.",
                }
            )
            ja_blob = synthetic_locale_blob(
                {
                    "Glossary.TAB[OfficeZones]": "オフィス区画",
                    "Glossary.SECTION_TITLE[OfficeZones]": "オフィス区画",
                    "Glossary.SECTION_CONTENT[OfficeZones]": "日本語の説明です。",
                }
            )
            with zipfile.ZipFile(locale, "w") as archive:
                archive.writestr("en-US.loc", en_blob)
                archive.writestr("ja-JP.loc", ja_blob)

            source = GameEncyclopediaSource.load(
                EncyclopediaConfig(locale_cok=locale, locale="en-US", cache_dir=root / "cache"),
                steam_roots=[],
            )

            self.assertTrue(source.available)
            entry = source.get_entry("officezones")
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry["title"], "Office Zones")
            self.assertIn("educated workers", entry["text"])
            self.assertNotIn("日本語", entry["text"])

    def test_source_rebuilds_cache_then_searches_entries(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(
                synthetic_locale_blob(
                    {
                        "Glossary.TAB[Roads]": "Roads",
                        "Glossary.CATEGORY[RoadBasics]": "Road Basics",
                        "Glossary.SECTION_TITLE[Roads.RoadBasics.Roads]": "Roads",
                        "Glossary.SECTION_CONTENT[Roads.RoadBasics.Roads]": "Roads connect buildings and zones.",
                    }
                )
            )
            source = GameEncyclopediaSource.load(
                EncyclopediaConfig(locale_cok=locale, cache_dir=root / "cache"),
                steam_roots=[],
            )

            self.assertTrue(source.available)
            self.assertEqual(source.cache_status, "rebuilt")
            results = source.search("connect zones", limit=3)
            self.assertEqual(results[0]["entry_id"], "roads.roadbasics.roads")
            self.assertEqual(results[0]["source"], "game_encyclopedia")

            second = GameEncyclopediaSource.load(
                EncyclopediaConfig(locale_cok=locale, cache_dir=root / "cache"),
                steam_roots=[],
            )
            self.assertEqual(second.cache_status, "hit")

    def test_zero_entry_source_status_reports_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(synthetic_locale_blob({"Glossary.TAB[Roads]": "Roads"}))

            source = GameEncyclopediaSource.load(
                EncyclopediaConfig(locale_cok=locale, cache_dir=root / "cache"),
                steam_roots=[],
            )

            self.assertFalse(source.available)
            self.assertFalse(source.status()["available"])
            self.assertIn("no glossary entries", source.status()["warning"])
            self.assertEqual(source.status()["locale_cok_path"], str(locale.resolve()))
            self.assertEqual(source.status()["cache_status"], "rebuilt")
            self.assertEqual(source.status()["entry_count"], 0)

    def test_semantically_invalid_cache_rows_are_rebuilt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locale = root / "Locale.cok"
            locale.write_bytes(
                synthetic_locale_blob(
                    {
                        "Glossary.TAB[Roads]": "Roads",
                        "Glossary.CATEGORY[RoadBasics]": "Road Basics",
                        "Glossary.SECTION_TITLE[Roads.RoadBasics.Roads]": "Roads",
                        "Glossary.SECTION_CONTENT[Roads.RoadBasics.Roads]": "Roads connect buildings and zones.",
                    }
                )
            )
            discovery = find_locale_cok(EncyclopediaConfig(locale_cok=locale), steam_roots=[])
            fingerprint = current_source_fingerprint(discovery, locale="en-US")
            write_cache(root / "cache", fingerprint, [{"title": "Bad"}], chunks=[{"text": "Bad"}])

            source = GameEncyclopediaSource.load(
                EncyclopediaConfig(locale_cok=locale, cache_dir=root / "cache"),
                steam_roots=[],
            )

            self.assertEqual(source.cache_status, "rebuilt")
            self.assertIsNotNone(source.get_entry("roads.roadbasics.roads"))
            self.assertNotIn("None", source.entries_by_id)

    def test_unavailable_source_search_returns_empty_list(self) -> None:
        with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": "", "CITIES2_LOCALE_COK": ""}, clear=False):
            source = GameEncyclopediaSource.load(EncyclopediaConfig(), steam_roots=[])

        self.assertFalse(source.available)
        self.assertEqual(source.search("roads"), [])
        self.assertEqual(source.get_entry("roads"), None)


if __name__ == "__main__":
    unittest.main()
