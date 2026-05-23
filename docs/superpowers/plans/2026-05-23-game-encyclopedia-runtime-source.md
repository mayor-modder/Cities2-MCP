# Game Encyclopedia Runtime Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional-by-availability, enabled-by-default MCP source that reads the Cities: Skylines II in-game Encyclopedia from the user's local game files without redistributing game text.

**Architecture:** Add a focused `server/game_encyclopedia.py` module that handles discovery, synthetic-testable parsing, conservative cleanup, cache validation, and search indexing. Wire it into `server/mcp_server.py` as separate `search_encyclopedia`, `get_encyclopedia_entry`, and `source_status` tools while keeping existing wiki search behavior unchanged.

**Tech Stack:** Python standard library, current MCP stdio server code, existing `HybridIndex` ranking from `server/retrieval/mcp_server.py`, `unittest`, JSONL cache files.

---

## File Structure

- Create `server/game_encyclopedia.py`: discovery, VDF parsing, source metadata, cache read/write, synthetic-friendly `Locale.cok` Glossary parser, markup cleanup, in-memory source object, and tool payload helpers.
- Modify `server/mcp_server.py`: CLI/env config, source initialization, tool catalog additions, tool handling, resource listing/read support, and warning text in initialization instructions.
- Modify `tests/smoke_mcp.py`: verify new tools are listed and unavailable local game source does not break smoke tests.
- Create `tests/test_game_encyclopedia.py`: unit tests for discovery, precedence, cache validation, parser, cleanup, indexing, and unavailable status.
- Create `tests/test_mcp_game_encyclopedia.py`: MCP-level tests for tool catalog, status payloads, unavailable errors, and synthetic-cache search.
- Modify `README.md`: document local game Encyclopedia support and non-redistribution.
- Modify `INSTALL.md`: add setup discovery notes and environment override guidance.
- Modify `.gitignore`: ignore local game Encyclopedia cache/output patterns if they can appear under the repo during development.

## Task 1: Add Discovery And Status Model

**Files:**
- Create: `server/game_encyclopedia.py`
- Test: `tests/test_game_encyclopedia.py`

- [ ] **Step 1: Write failing tests for explicit path precedence and missing status**

Add this test file:

```python
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

    def test_game_dir_env_resolves_locale_cok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            game_dir = Path(td) / "Cities Skylines II"
            locale = game_dir / "Cities2_Data" / "Content" / "Game" / "Locale.cok"
            locale.parent.mkdir(parents=True)
            locale.write_bytes(b"game")

            with mock.patch.dict(os.environ, {"CITIES2_GAME_DIR": str(game_dir)}, clear=False):
                result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, locale)
        self.assertEqual(result.source_kind, "env_game_dir")

    def test_missing_source_returns_nonfatal_warning_status(self) -> None:
        result = find_locale_cok(EncyclopediaConfig(), steam_roots=[])
        payload = source_status_payload(result, cache_status="unavailable", entry_count=0)

        self.assertFalse(payload["available"])
        self.assertEqual(payload["warning"], GAME_ENCYCLOPEDIA_WARNING)
        self.assertEqual(payload["cache_status"], "unavailable")
        self.assertEqual(payload["entry_count"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'game_encyclopedia'`.

- [ ] **Step 3: Implement discovery model and precedence**

Create `server/game_encyclopedia.py` with:

```python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

JSON = Dict[str, Any]
APP_ID = "949230"
EXTRACTOR_VERSION = "1"
GAME_ENCYCLOPEDIA_WARNING = (
    "Game Encyclopedia not found. Wiki search is still available. "
    "Set CITIES2_GAME_DIR or CITIES2_LOCALE_COK to enable local game Encyclopedia search."
)
RELATIVE_LOCALE_COK = Path("Cities2_Data") / "Content" / "Game" / "Locale.cok"


@dataclass(frozen=True)
class EncyclopediaConfig:
    game_dir: Optional[Path] = None
    locale_cok: Optional[Path] = None
    locale: str = "en-US"
    cache_dir: Optional[Path] = None


@dataclass(frozen=True)
class LocaleDiscovery:
    available: bool
    locale_cok_path: Optional[Path] = None
    game_dir: Optional[Path] = None
    source_kind: str = "missing"
    steam_app_id: Optional[str] = None
    steam_build_id: Optional[str] = None
    warning: str = GAME_ENCYCLOPEDIA_WARNING


def _existing_locale_file(path: Optional[Path]) -> Optional[Path]:
    if path is None:
        return None
    candidate = path.expanduser()
    if candidate.is_file():
        return candidate.resolve()
    return None


def _locale_from_game_dir(path: Optional[Path]) -> Optional[Path]:
    if path is None:
        return None
    return _existing_locale_file(path.expanduser() / RELATIVE_LOCALE_COK)


def _available(
    locale_cok: Path,
    *,
    source_kind: str,
    game_dir: Optional[Path] = None,
    steam_build_id: Optional[str] = None,
) -> LocaleDiscovery:
    resolved_locale = locale_cok.resolve()
    resolved_game_dir = game_dir.resolve() if game_dir is not None else resolved_locale.parents[4]
    return LocaleDiscovery(
        available=True,
        locale_cok_path=resolved_locale,
        game_dir=resolved_game_dir,
        source_kind=source_kind,
        steam_app_id=APP_ID if steam_build_id else None,
        steam_build_id=steam_build_id,
        warning="",
    )


def default_steam_roots() -> List[Path]:
    roots: List[Path] = []
    if os.name == "nt":
        roots.append(Path(r"C:\Program Files (x86)\Steam"))
    elif sys.platform == "darwin":
        roots.append(Path.home() / "Library" / "Application Support" / "Steam")
    else:
        roots.append(Path.home() / ".steam" / "steam")
        roots.append(Path.home() / ".local" / "share" / "Steam")
    return roots


def find_locale_cok(
    config: EncyclopediaConfig,
    *,
    steam_roots: Optional[Iterable[Path]] = None,
) -> LocaleDiscovery:
    direct = _existing_locale_file(config.locale_cok)
    if direct is not None:
        return _available(direct, source_kind="explicit_locale_cok")

    env_direct = _existing_locale_file(Path(os.environ["CITIES2_LOCALE_COK"])) if os.environ.get("CITIES2_LOCALE_COK") else None
    if env_direct is not None:
        return _available(env_direct, source_kind="env_locale_cok")

    from_cli_game = _locale_from_game_dir(config.game_dir)
    if from_cli_game is not None:
        return _available(from_cli_game, source_kind="explicit_game_dir", game_dir=config.game_dir)

    env_game_dir_value = os.environ.get("CITIES2_GAME_DIR")
    env_game_dir = Path(env_game_dir_value) if env_game_dir_value else None
    from_env_game = _locale_from_game_dir(env_game_dir)
    if from_env_game is not None:
        return _available(from_env_game, source_kind="env_game_dir", game_dir=env_game_dir)

    for steam_root in steam_roots if steam_roots is not None else default_steam_roots():
        result = discover_steam_locale(steam_root)
        if result.available:
            return result

    return LocaleDiscovery(available=False)


def discover_steam_locale(steam_root: Path) -> LocaleDiscovery:
    return LocaleDiscovery(available=False)


def source_status_payload(
    discovery: LocaleDiscovery,
    *,
    cache_status: str,
    entry_count: int,
) -> JSON:
    return {
        "source": "game_encyclopedia",
        "available": discovery.available,
        "warning": "" if discovery.available else GAME_ENCYCLOPEDIA_WARNING,
        "source_kind": discovery.source_kind,
        "locale_cok_path": str(discovery.locale_cok_path or ""),
        "game_dir": str(discovery.game_dir or ""),
        "steam_app_id": discovery.steam_app_id or "",
        "steam_build_id": discovery.steam_build_id or "",
        "cache_status": cache_status,
        "entry_count": entry_count,
    }
```

- [ ] **Step 4: Run tests to verify Task 1 passes**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia -v
```

Expected: PASS for the three discovery tests.

- [ ] **Step 5: Commit**

```powershell
git add server/game_encyclopedia.py tests/test_game_encyclopedia.py
git commit -m "Add game encyclopedia discovery status"
```

## Task 2: Add Steam Library Discovery

**Files:**
- Modify: `server/game_encyclopedia.py`
- Test: `tests/test_game_encyclopedia.py`

- [ ] **Step 1: Add failing tests for Steam VDF and build id**

Append to `GameEncyclopediaDiscoveryTests`:

```python
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

            result = find_locale_cok(EncyclopediaConfig(), steam_roots=[steam_root])

        self.assertTrue(result.available)
        self.assertEqual(result.locale_cok_path, locale.resolve())
        self.assertEqual(result.source_kind, "steam")
        self.assertEqual(result.steam_app_id, "949230")
        self.assertEqual(result.steam_build_id, "23061229")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaDiscoveryTests.test_steam_libraryfolders_vdf_discovers_secondary_library -v
```

Expected: FAIL because `discover_steam_locale` currently returns unavailable.

- [ ] **Step 3: Implement VDF path and build id parsing**

Add to `server/game_encyclopedia.py`:

```python
import re
```

Add these helpers above `discover_steam_locale`:

```python
_VDF_PATH_RE = re.compile(r'"path"\s+"(?P<path>(?:\\.|[^"])*)"')
_VDF_BUILD_RE = re.compile(r'"buildid"\s+"(?P<buildid>\d+)"')


def _decode_vdf_string(value: str) -> str:
    return value.replace("\\\\", "\\")


def steam_libraries(steam_root: Path) -> List[Path]:
    libraries: List[Path] = []
    if steam_root.exists():
        libraries.append(steam_root.resolve())

    vdf = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf.is_file():
        return libraries

    text = vdf.read_text(encoding="utf-8", errors="replace")
    for match in _VDF_PATH_RE.finditer(text):
        candidate = Path(_decode_vdf_string(match.group("path"))).expanduser()
        if candidate.exists():
            resolved = candidate.resolve()
            if resolved not in libraries:
                libraries.append(resolved)
    return libraries


def read_steam_build_id(library: Path) -> Optional[str]:
    manifest = library / "steamapps" / f"appmanifest_{APP_ID}.acf"
    if not manifest.is_file():
        return None
    text = manifest.read_text(encoding="utf-8", errors="replace")
    match = _VDF_BUILD_RE.search(text)
    return match.group("buildid") if match else None
```

Replace `discover_steam_locale` with:

```python
def discover_steam_locale(steam_root: Path) -> LocaleDiscovery:
    for library in steam_libraries(steam_root.expanduser()):
        game_dir = library / "steamapps" / "common" / "Cities Skylines II"
        locale = _locale_from_game_dir(game_dir)
        if locale is None:
            continue
        return _available(
            locale,
            source_kind="steam",
            game_dir=game_dir,
            steam_build_id=read_steam_build_id(library),
        )
    return LocaleDiscovery(available=False)
```

- [ ] **Step 4: Run discovery tests**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaDiscoveryTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/game_encyclopedia.py tests/test_game_encyclopedia.py
git commit -m "Discover Steam game encyclopedia source"
```

## Task 3: Add Cache Validation And JSONL IO

**Files:**
- Modify: `server/game_encyclopedia.py`
- Test: `tests/test_game_encyclopedia.py`

- [ ] **Step 1: Add failing cache tests**

Append below the discovery tests:

```python
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
```

- [ ] **Step 2: Run cache tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaCacheTests -v
```

Expected: FAIL due missing cache functions.

- [ ] **Step 3: Implement cache functions**

Add imports:

```python
import json
import time
```

Add to `server/game_encyclopedia.py`:

```python
def cache_dir_default() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / "Cities2-MCP" / "cache" / "game-encyclopedia"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Cities2-MCP" / "game-encyclopedia"
    base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return base / "cities2-mcp" / "game-encyclopedia"


def current_source_fingerprint(discovery: LocaleDiscovery, *, locale: str) -> JSON:
    if not discovery.available or discovery.locale_cok_path is None:
        return {
            "extractor_version": EXTRACTOR_VERSION,
            "locale": locale,
            "available": False,
        }
    stat = discovery.locale_cok_path.stat()
    return {
        "extractor_version": EXTRACTOR_VERSION,
        "locale": locale,
        "locale_cok_path": str(discovery.locale_cok_path),
        "locale_cok_size": stat.st_size,
        "locale_cok_mtime_ns": stat.st_mtime_ns,
        "steam_app_id": discovery.steam_app_id or "",
        "steam_build_id": discovery.steam_build_id or "",
    }


def _manifest_path(cache_dir: Path) -> Path:
    return cache_dir / "manifest.json"


def cache_is_fresh(cache_dir: Path, fingerprint: JSON) -> bool:
    manifest_path = _manifest_path(cache_dir)
    entries_path = cache_dir / "entries.jsonl"
    chunks_path = cache_dir / "chunks.jsonl"
    if not manifest_path.is_file() or not entries_path.is_file() or not chunks_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    cached = manifest.get("fingerprint")
    return cached == fingerprint


def _write_jsonl(path: Path, rows: List[JSON]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def _read_jsonl(path: Path) -> List[JSON]:
    rows: List[JSON] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_cache(cache_dir: Path, fingerprint: JSON, entries: List[JSON], *, chunks: List[JSON]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(cache_dir / "entries.jsonl", entries)
    _write_jsonl(cache_dir / "chunks.jsonl", chunks)
    manifest = {
        "fingerprint": fingerprint,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entry_count": len(entries),
        "chunk_count": len(chunks),
    }
    _manifest_path(cache_dir).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_cached_entries(cache_dir: Path) -> List[JSON]:
    return _read_jsonl(cache_dir / "entries.jsonl")


def load_cached_chunks(cache_dir: Path) -> List[JSON]:
    return _read_jsonl(cache_dir / "chunks.jsonl")
```

- [ ] **Step 4: Run cache tests**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaCacheTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/game_encyclopedia.py tests/test_game_encyclopedia.py
git commit -m "Add game encyclopedia cache validation"
```

## Task 4: Add Glossary Parser And Cleanup

**Files:**
- Modify: `server/game_encyclopedia.py`
- Test: `tests/test_game_encyclopedia.py`

- [ ] **Step 1: Add synthetic parser and cleanup tests**

Append to `tests/test_game_encyclopedia.py`:

```python
from game_encyclopedia import (  # noqa: E402
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

    def test_clean_markup_text_removes_retrieval_noise(self) -> None:
        cleaned = clean_markup_text(
            "**Roads**\r\n<image:Media/Game/Glossary/Roads.png>\r\n"
            "Press <inputAction:Tool.Select> near <icon:Roads>."
        )

        self.assertEqual(cleaned, "Roads\nPress Tool.Select near Roads.")
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaParserTests -v
```

Expected: FAIL due missing parser functions.

- [ ] **Step 3: Implement varint scanning, parser, entry builder, and cleanup**

Add imports:

```python
from collections import OrderedDict
```

Add to `server/game_encyclopedia.py`:

```python
_GLOSSARY_PREFIX = "Glossary."
_IMAGE_RE = re.compile(r"<image:([^>]+)>")
_ICON_RE = re.compile(r"<icon:([^>]+)>")
_INPUT_ACTION_RE = re.compile(r"<inputAction:([^>]+)>")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_SECTION_RE = re.compile(r"^Glossary\.SECTION_(TITLE|CONTENT)\[(?P<id>[^\]]+)\]$")
_TAB_RE = re.compile(r"^Glossary\.TAB\[(?P<id>[^\]]+)\]$")
_CATEGORY_RE = re.compile(r"^Glossary\.CATEGORY\[(?P<id>[^\]]+)\]$")


def _read_varint(data: bytes, offset: int) -> Optional[tuple[int, int]]:
    value = 0
    shift = 0
    pos = offset
    while pos < len(data) and shift <= 28:
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    return None


def _read_utf8_field(data: bytes, offset: int) -> Optional[tuple[str, int]]:
    parsed = _read_varint(data, offset)
    if parsed is None:
        return None
    length, pos = parsed
    if length < 0 or length > 500_000:
        return None
    end = pos + length
    if end > len(data):
        return None
    try:
        return data[pos:end].decode("utf-8"), end
    except UnicodeDecodeError:
        return None


def extract_glossary_records(data: bytes) -> "OrderedDict[str, str]":
    records: "OrderedDict[str, str]" = OrderedDict()
    offset = 0
    while offset < len(data):
        key_field = _read_utf8_field(data, offset)
        if key_field is None:
            offset += 1
            continue
        key, after_key = key_field
        if not key.startswith(_GLOSSARY_PREFIX):
            offset += 1
            continue
        value_field = _read_utf8_field(data, after_key)
        if value_field is None:
            offset += 1
            continue
        value, after_value = value_field
        records[key] = value
        offset = after_value
    return records


def _display_token(value: str) -> str:
    token = value.rsplit("/", 1)[-1]
    token = token.rsplit(".", 1)[0]
    return token.strip()


def clean_markup_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = _BOLD_RE.sub(r"\1", cleaned)
    cleaned = _IMAGE_RE.sub("", cleaned)
    cleaned = _INPUT_ACTION_RE.sub(lambda m: _display_token(m.group(1)), cleaned)
    cleaned = _ICON_RE.sub(lambda m: _display_token(m.group(1)), cleaned)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _entry_id(raw_id: str) -> str:
    return raw_id.strip().lower()


def _split_section_id(raw_id: str) -> tuple[str, str]:
    parts = raw_id.split(".")
    tab_key = parts[0] if parts else ""
    category_key = parts[1] if len(parts) > 1 else ""
    return tab_key, category_key


def records_to_entries(records: "OrderedDict[str, str]", *, locale: str, source_metadata: JSON) -> List[JSON]:
    tabs: Dict[str, str] = {}
    categories: Dict[str, str] = {}
    titles: Dict[str, str] = {}
    contents: Dict[str, str] = {}

    for key, value in records.items():
        tab_match = _TAB_RE.match(key)
        if tab_match:
            tabs[tab_match.group("id")] = value.strip()
            continue
        category_match = _CATEGORY_RE.match(key)
        if category_match:
            categories[category_match.group("id")] = value.strip()
            continue
        section_match = _SECTION_RE.match(key)
        if section_match:
            section_id = section_match.group("id")
            if "TITLE" in key:
                titles[section_id] = value.strip()
            else:
                contents[section_id] = value

    entries: List[JSON] = []
    for section_id, raw_content in contents.items():
        title = titles.get(section_id, section_id.rsplit(".", 1)[-1]).strip()
        tab_key, category_key = _split_section_id(section_id)
        text = clean_markup_text(raw_content)
        entry = {
            "entry_id": _entry_id(section_id),
            "source": "game_encyclopedia",
            "source_key": f"Glossary.SECTION_CONTENT[{section_id}]",
            "title": title,
            "tab": tabs.get(tab_key, tab_key),
            "category": categories.get(category_key, category_key),
            "raw_content": raw_content,
            "text": text,
            "locale": locale,
            "metadata": dict(source_metadata),
        }
        entries.append(entry)
    entries.sort(key=lambda item: (str(item["tab"]), str(item["category"]), str(item["title"])))
    return entries
```

- [ ] **Step 4: Run parser tests**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaParserTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/game_encyclopedia.py tests/test_game_encyclopedia.py
git commit -m "Parse local game encyclopedia glossary"
```

## Task 5: Add Source Loader And Search Index

**Files:**
- Modify: `server/game_encyclopedia.py`
- Test: `tests/test_game_encyclopedia.py`

- [ ] **Step 1: Add failing tests for load, rebuild, cache reuse, and search**

Append to `tests/test_game_encyclopedia.py`:

```python
from game_encyclopedia import GameEncyclopediaSource  # noqa: E402


class GameEncyclopediaSourceTests(unittest.TestCase):
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

    def test_unavailable_source_search_returns_empty_list(self) -> None:
        source = GameEncyclopediaSource.load(EncyclopediaConfig(), steam_roots=[])

        self.assertFalse(source.available)
        self.assertEqual(source.search("roads"), [])
        self.assertEqual(source.get_entry("roads"), None)
```

- [ ] **Step 2: Run source tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia.GameEncyclopediaSourceTests -v
```

Expected: FAIL due missing `GameEncyclopediaSource`.

- [ ] **Step 3: Implement source object and search**

Add import:

```python
from retrieval.mcp_server import HybridIndex
```

Add to `server/game_encyclopedia.py`:

```python
def _source_metadata(discovery: LocaleDiscovery) -> JSON:
    return {
        "locale_cok_path": str(discovery.locale_cok_path or ""),
        "game_dir": str(discovery.game_dir or ""),
        "steam_app_id": discovery.steam_app_id or "",
        "steam_build_id": discovery.steam_build_id or "",
    }


def entries_to_chunks(entries: List[JSON]) -> List[JSON]:
    chunks: List[JSON] = []
    for entry in entries:
        chunks.append(
            {
                "chunk_id": f"game_encyclopedia:{entry['entry_id']}",
                "entry_id": entry["entry_id"],
                "source": "game_encyclopedia",
                "title": entry["title"],
                "tab": entry["tab"],
                "category": entry["category"],
                "text": "\n".join(
                    [
                        str(entry["title"]),
                        str(entry["tab"]),
                        str(entry["category"]),
                        str(entry["text"]),
                    ]
                ).strip(),
                "locale": entry["locale"],
                "metadata": entry["metadata"],
            }
        )
    return chunks


class GameEncyclopediaSource:
    def __init__(
        self,
        *,
        discovery: LocaleDiscovery,
        cache_status: str,
        entries: List[JSON],
        chunks: List[JSON],
    ) -> None:
        self.discovery = discovery
        self.cache_status = cache_status
        self.entries = entries
        self.chunks = chunks
        self.entries_by_id = {str(entry.get("entry_id")): entry for entry in entries}
        self.index = HybridIndex(chunks, text_key="text") if chunks else None

    @property
    def available(self) -> bool:
        return self.discovery.available and bool(self.entries)

    @classmethod
    def load(
        cls,
        config: EncyclopediaConfig,
        *,
        steam_roots: Optional[Iterable[Path]] = None,
    ) -> "GameEncyclopediaSource":
        discovery = find_locale_cok(config, steam_roots=steam_roots)
        if not discovery.available or discovery.locale_cok_path is None:
            return cls(discovery=discovery, cache_status="unavailable", entries=[], chunks=[])

        cache_dir = config.cache_dir or cache_dir_default()
        fingerprint = current_source_fingerprint(discovery, locale=config.locale)
        if cache_is_fresh(cache_dir, fingerprint):
            entries = load_cached_entries(cache_dir)
            chunks = load_cached_chunks(cache_dir)
            return cls(discovery=discovery, cache_status="hit", entries=entries, chunks=chunks)

        data = discovery.locale_cok_path.read_bytes()
        records = extract_glossary_records(data)
        entries = records_to_entries(records, locale=config.locale, source_metadata=_source_metadata(discovery))
        chunks = entries_to_chunks(entries)
        write_cache(cache_dir, fingerprint, entries, chunks=chunks)
        return cls(discovery=discovery, cache_status="rebuilt", entries=entries, chunks=chunks)

    def status(self) -> JSON:
        return source_status_payload(self.discovery, cache_status=self.cache_status, entry_count=len(self.entries))

    def search(self, query: str, *, limit: int = 5) -> List[JSON]:
        if self.index is None:
            return []
        matches = self.index.search(query, limit=limit, title_key="title")
        results: List[JSON] = []
        for score, chunk in matches:
            entry_id = str(chunk.get("entry_id", ""))
            results.append(
                {
                    "score": round(score, 4),
                    "source": "game_encyclopedia",
                    "entry_id": entry_id,
                    "title": chunk.get("title"),
                    "tab": chunk.get("tab"),
                    "category": chunk.get("category"),
                    "snippet": str(chunk.get("text", ""))[:900],
                    "metadata": chunk.get("metadata", {}),
                }
            )
        return results

    def get_entry(self, entry_id: str) -> Optional[JSON]:
        return self.entries_by_id.get(entry_id)
```

- [ ] **Step 4: Run all game encyclopedia unit tests**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/game_encyclopedia.py tests/test_game_encyclopedia.py
git commit -m "Index local game encyclopedia source"
```

## Task 6: Wire MCP Tools And Resources

**Files:**
- Modify: `server/mcp_server.py`
- Test: `tests/test_mcp_game_encyclopedia.py`

- [ ] **Step 1: Add failing MCP tool tests**

Create `tests/test_mcp_game_encyclopedia.py`:

```python
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class McpGameEncyclopediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module("mcp_server_game_encyclopedia_tests", ROOT / "server" / "mcp_server.py")

    def test_tools_list_includes_game_encyclopedia_tools(self) -> None:
        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error="docs missing",
            workflow_error=None,
            docs_paths={},
        )

        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("search_encyclopedia", names)
        self.assertIn("get_encyclopedia_entry", names)
        self.assertIn("source_status", names)

    def test_source_status_reports_unavailable_encyclopedia(self) -> None:
        response = self.module.handle_tools_call(
            2,
            {"name": "source_status", "arguments": {}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error="docs missing",
            workflow_error=None,
            docs_paths={},
        )
        payload = json.loads(response["result"]["content"][0]["text"])

        self.assertFalse(payload["game_encyclopedia"]["available"])
        self.assertIn("Game Encyclopedia not found", payload["game_encyclopedia"]["warning"])

    def test_search_encyclopedia_unavailable_returns_tool_error_payload(self) -> None:
        response = self.module.handle_tools_call(
            3,
            {"name": "search_encyclopedia", "arguments": {"query": "roads"}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )
        payload = json.loads(response["result"]["content"][0]["text"])

        self.assertFalse(payload["ok"])
        self.assertIn("Game Encyclopedia not found", payload["message"])
```

- [ ] **Step 2: Run MCP tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_mcp_game_encyclopedia -v
```

Expected: FAIL because `handle_request` and `handle_tools_call` do not accept `encyclopedia`, and tools are absent.

- [ ] **Step 3: Add MCP catalog and handlers**

Modify imports in `server/mcp_server.py`:

```python
from game_encyclopedia import (
    GAME_ENCYCLOPEDIA_WARNING,
    EncyclopediaConfig,
    GameEncyclopediaSource,
)
```

Add constants near docs guard constants:

```python
ENCYCLOPEDIA_TOOL_NAMES = {"search_encyclopedia", "get_encyclopedia_entry", "source_status"}
```

Add catalog:

```python
def encyclopedia_tools_catalog() -> List[JSON]:
    return [
        {
            "name": "search_encyclopedia",
            "description": "Search the local Cities: Skylines II in-game Encyclopedia read from the user's installed game files.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_encyclopedia_entry",
            "description": "Return one local Cities: Skylines II in-game Encyclopedia entry by entry_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"entry_id": {"type": "string"}},
                "required": ["entry_id"],
            },
        },
        {
            "name": "source_status",
            "description": "Report Cities2-MCP source availability for the wiki corpus and local game Encyclopedia.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]
```

Add handler:

```python
def encyclopedia_unavailable_result() -> JSON:
    return text_result({"ok": False, "message": GAME_ENCYCLOPEDIA_WARNING}, is_error=True)


def handle_encyclopedia_tools(
    req_id: object,
    params: JSON,
    *,
    corpus: Optional[Corpus],
    encyclopedia: Optional[GameEncyclopediaSource],
    corpus_error: Optional[str],
    docs_paths: Optional[Dict[str, str]],
) -> Optional[JSON]:
    name = str(params.get("name", ""))
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}

    if name == "source_status":
        wiki_status = {
            "source": "wiki",
            "available": corpus is not None,
            "error": corpus_error or "",
            "configured_paths": docs_paths or {},
        }
        game_status = encyclopedia.status() if encyclopedia is not None else {
            "source": "game_encyclopedia",
            "available": False,
            "warning": GAME_ENCYCLOPEDIA_WARNING,
            "cache_status": "unavailable",
            "entry_count": 0,
        }
        return {"jsonrpc": "2.0", "id": req_id, "result": text_result({"wiki": wiki_status, "game_encyclopedia": game_status})}

    if name == "search_encyclopedia":
        if encyclopedia is None or not encyclopedia.available:
            return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result()}
        query = str(args.get("query", "")).strip()
        limit = max(1, min(20, int(args.get("limit", 5) or 5)))
        if not query:
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result({"ok": False, "message": "Missing query"}, is_error=True)}
        results = encyclopedia.search(query, limit=limit)
        return {"jsonrpc": "2.0", "id": req_id, "result": text_result({"ok": True, "query": query, "count": len(results), "results": results})}

    if name == "get_encyclopedia_entry":
        if encyclopedia is None or not encyclopedia.available:
            return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result()}
        entry_id = str(args.get("entry_id", "")).strip()
        entry = encyclopedia.get_entry(entry_id)
        if entry is None:
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result({"ok": False, "message": f"Entry not found: {entry_id}"}, is_error=True)}
        payload = dict(entry)
        payload["ok"] = True
        return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

    return None
```

Update `handle_tools_call` signature to include `encyclopedia: Optional[GameEncyclopediaSource] = None`, call `handle_encyclopedia_tools` before retrieval delegation, and include `encyclopedia_tools_catalog()` in `extra_tools_catalog`.

Update `handle_request` signature to include `encyclopedia: Optional[GameEncyclopediaSource] = None`, pass it through all internal `handle_tools_call` calls, and include the tools catalog for `tools/list`.

- [ ] **Step 4: Run MCP tests**

Run:

```powershell
python -m unittest tests.test_mcp_game_encyclopedia -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/mcp_server.py tests/test_mcp_game_encyclopedia.py
git commit -m "Expose game encyclopedia MCP tools"
```

## Task 7: Add Startup Configuration, Resources, And Smoke Coverage

**Files:**
- Modify: `server/mcp_server.py`
- Modify: `tests/smoke_mcp.py`
- Test: `tests/test_mcp_game_encyclopedia.py`

- [ ] **Step 1: Add failing resource test**

Append to `McpGameEncyclopediaTests`:

```python
    def test_resources_list_includes_encyclopedia_entries_when_available(self) -> None:
        encyclopedia = type(
            "FakeEncyclopedia",
            (),
            {
                "available": True,
                "entries": [{"entry_id": "roads", "title": "Roads"}],
                "get_entry": lambda self, entry_id: {"entry_id": entry_id, "title": "Roads", "text": "Road text"},
                "status": lambda self: {"source": "game_encyclopedia", "available": True, "entry_count": 1},
            },
        )()

        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=encyclopedia,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        uris = {item["uri"] for item in response["result"]["resources"]}
        self.assertIn("cities2encyclopedia://entry/roads", uris)
```

- [ ] **Step 2: Run resource test to verify it fails**

Run:

```powershell
python -m unittest tests.test_mcp_game_encyclopedia.McpGameEncyclopediaTests.test_resources_list_includes_encyclopedia_entries_when_available -v
```

Expected: FAIL because resources only include wiki resources.

- [ ] **Step 3: Implement resource helpers and startup load**

Add to `server/mcp_server.py`:

```python
def encyclopedia_resource_catalog(encyclopedia: Optional[GameEncyclopediaSource]) -> List[JSON]:
    if encyclopedia is None or not encyclopedia.available:
        return []
    resources: List[JSON] = []
    for entry in encyclopedia.entries:
        entry_id = str(entry.get("entry_id", "")).strip()
        if not entry_id:
            continue
        resources.append(
            {
                "uri": f"cities2encyclopedia://entry/{entry_id}",
                "name": str(entry.get("title") or entry_id),
                "description": f"game encyclopedia entry: {entry_id}",
                "mimeType": "application/json",
            }
        )
    return resources


def handle_encyclopedia_resource_read(req_id: object, uri: str, encyclopedia: Optional[GameEncyclopediaSource]) -> Optional[JSON]:
    prefix = "cities2encyclopedia://entry/"
    if not uri.startswith(prefix):
        return None
    if encyclopedia is None or not encyclopedia.available:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": GAME_ENCYCLOPEDIA_WARNING}}
    entry_id = uri[len(prefix):]
    entry = encyclopedia.get_entry(entry_id)
    if entry is None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32002, "message": f"Entry not found: {entry_id}"}}
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(entry, ensure_ascii=False, indent=2),
                }
            ]
        },
    }
```

In `handle_request`, update `resources/list` to extend with `encyclopedia_resource_catalog(encyclopedia)`. In `resources/read`, call `handle_encyclopedia_resource_read` before the wiki read path.

In `main`, add parser arguments:

```python
    parser.add_argument("--game-dir")
    parser.add_argument("--locale-cok")
    parser.add_argument("--encyclopedia-cache-dir")
```

Initialize:

```python
    encyclopedia: Optional[GameEncyclopediaSource] = None
    try:
        encyclopedia = GameEncyclopediaSource.load(
            EncyclopediaConfig(
                game_dir=Path(args.game_dir) if args.game_dir else None,
                locale_cok=Path(args.locale_cok) if args.locale_cok else None,
                cache_dir=Path(args.encyclopedia_cache_dir) if args.encyclopedia_cache_dir else None,
            )
        )
    except Exception as exc:
        debug_log(f"Game encyclopedia init failed: {exc}")
        encyclopedia = None
```

Pass `encyclopedia=encyclopedia` into all `handle_request` calls in `main`.

- [ ] **Step 4: Update smoke test tool expectations**

In `tests/smoke_mcp.py`, add the new tool names to the expected list:

```python
    "search_encyclopedia",
    "get_encyclopedia_entry",
    "source_status",
```

Add a source-status call to the smoke sequence:

```python
status = call_tool(proc, "source_status", {})
assert "game_encyclopedia" in status
```

Use the existing helper style in `tests/smoke_mcp.py`; do not add a hard requirement for a local game install.

- [ ] **Step 5: Run MCP and smoke tests**

Run:

```powershell
python -m unittest tests.test_mcp_game_encyclopedia -v
python tests\smoke_mcp.py
```

Expected: both PASS, including on a machine without a local game install.

- [ ] **Step 6: Commit**

```powershell
git add server/mcp_server.py tests/test_mcp_game_encyclopedia.py tests/smoke_mcp.py
git commit -m "Load game encyclopedia source at startup"
```

## Task 8: Update Documentation And Ignore Local Outputs

**Files:**
- Modify: `README.md`
- Modify: `INSTALL.md`
- Modify: `.gitignore`
- Test: manual text scan

- [ ] **Step 1: Update `.gitignore`**

Add these lines:

```gitignore
# Local game Encyclopedia cache/previews; generated from a user's installed game files.
game-encyclopedia-cache/
data-game-encyclopedia/
*.Locale.cok
```

- [ ] **Step 2: Update README**

In `README.md`, add a subsection under game/modding information:

```markdown
### Search The Local Game Encyclopedia

When Cities: Skylines II is installed locally, Cities2-MCP also tries to read the in-game Encyclopedia from the user's own game files. This source is enabled by default when the server can find `Cities2_Data/Content/Game/Locale.cok`, especially for standard Steam installs.

The extracted Encyclopedia index is cached locally on the user's machine and rebuilt only when the source game file, detected Steam build id, locale, or extractor version changes. Extracted game text is not committed to this repository, shipped in releases, or part of the redistributed wiki corpus.

If the game install is not found automatically, set `CITIES2_GAME_DIR` to the Cities: Skylines II install directory or `CITIES2_LOCALE_COK` to the full `Locale.cok` path.
```

Add the new tools to the MCP tools list:

```markdown
- `search_encyclopedia(query, limit=5)`
- `get_encyclopedia_entry(entry_id)`
- `source_status()`
```

- [ ] **Step 3: Update INSTALL**

In `INSTALL.md` step 2, add `CITIES2_GAME_DIR` as optional:

```markdown
| `CITIES2_GAME_DIR` | Optional. Usually auto-detected for Steam installs. Set this only when `source_status()` reports that the Game Encyclopedia was not found. Point it at the Cities: Skylines II install directory, not the `Cities2_Data` directory. |
```

In the JSON/TOML config examples, do not require this env var. Add a note after each config shape:

```markdown
Do not add `CITIES2_GAME_DIR` unless automatic discovery fails or the user has a non-standard install location. If needed, add it to the MCP server environment with the game install directory as its value.
```

In Verify, mention:

```markdown
`source_status()` may report that the Game Encyclopedia is unavailable on machines without Cities: Skylines II installed. That is a warning, not an install failure.
```

- [ ] **Step 4: Scan docs for required licensing posture**

Run:

```powershell
Select-String -Path README.md,INSTALL.md -Pattern "Extracted game text is not committed","source_status","CITIES2_GAME_DIR"
```

Expected: output includes all three patterns.

- [ ] **Step 5: Commit**

```powershell
git add .gitignore README.md INSTALL.md
git commit -m "Document local game encyclopedia source"
```

## Task 9: Final Verification

**Files:**
- All changed files

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_game_encyclopedia -v
python -m unittest tests.test_mcp_game_encyclopedia -v
python tests\smoke_mcp.py
```

Expected: all PASS.

- [ ] **Step 2: Run full public repo test suite**

Run:

```powershell
python -m unittest discover -v
```

Expected: all tests PASS.

- [ ] **Step 3: Confirm no game text entered git**

Run:

```powershell
git grep -n "Glossary.SECTION_CONTENT\\|Roads connect buildings and zones\\|Game/Glossary" -- .
```

Expected: only synthetic test strings and parser code references appear; no extracted real game Encyclopedia prose appears.

- [ ] **Step 4: Inspect final diff**

Run:

```powershell
git status --short
git log --oneline -8
```

Expected: working tree clean after the task commits, with the implementation commits visible at the top.

## Self-Review

- Spec coverage: discovery, default enablement, explicit overrides, Steam build metadata, local cache invalidation, parser, cleanup, separate search tools, source status, non-fatal warning, resource URIs, docs, and no redistribution are all assigned to tasks.
- Red-flag scan: this plan avoids unresolved blanks and vague "add tests" language. Each task includes concrete tests, code shape, commands, and expected results.
- Type consistency: `EncyclopediaConfig`, `LocaleDiscovery`, `GameEncyclopediaSource`, `search_encyclopedia`, `get_encyclopedia_entry`, and `source_status` are named consistently across tests, implementation steps, and MCP wiring.
