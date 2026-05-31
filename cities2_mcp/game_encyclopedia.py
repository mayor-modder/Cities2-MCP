from __future__ import annotations

import json
import os
import re
import sys
import time
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .retrieval.mcp_server import HybridIndex

JSON = Dict[str, Any]
APP_ID = "949230"
EXTRACTOR_VERSION = "2"
GAME_ENCYCLOPEDIA_WARNING = (
    "Game encyclopedia not found. Wiki search is still available. "
    "Set CITIES2_GAME_DIR or CITIES2_LOCALE_COK to enable local game encyclopedia search."
)
RELATIVE_LOCALE_COK = Path("Cities2_Data") / "Content" / "Game" / "Locale.cok"
MAX_LOCALE_PAYLOAD_BYTES = 64 * 1024 * 1024
MAX_LOCALE_COMPRESSED_BYTES = 64 * 1024 * 1024
_GLOSSARY_PREFIX = "Glossary."
_IMAGE_RE = re.compile(r"<image:([^>]+)>")
_ICON_RE = re.compile(r"<icon:([^>]+)>")
_INPUT_ACTION_RE = re.compile(r"<inputAction:([^>]+)>")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_SECTION_RE = re.compile(r"^Glossary\.SECTION_(?P<kind>TITLE|CONTENT)\[(?P<id>[^\]]+)\]$")
_TAB_RE = re.compile(r"^Glossary\.TAB\[(?P<id>[^\]]+)\]$")
_CATEGORY_RE = re.compile(r"^Glossary\.CATEGORY\[(?P<id>[^\]]+)\]$")


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
    resolved_game_dir = (
        game_dir.resolve() if game_dir is not None else _game_dir_from_locale_path(resolved_locale)
    )
    return LocaleDiscovery(
        available=True,
        locale_cok_path=resolved_locale,
        game_dir=resolved_game_dir,
        source_kind=source_kind,
        steam_app_id=APP_ID if steam_build_id else None,
        steam_build_id=steam_build_id,
        warning="",
    )


def _game_dir_from_locale_path(locale_cok: Path) -> Optional[Path]:
    try:
        relative_parts = RELATIVE_LOCALE_COK.parts
        if locale_cok.parts[-len(relative_parts):] == relative_parts:
            return locale_cok.parents[len(relative_parts) - 1]
    except IndexError:
        return None
    return None


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


_VDF_PATH_RE = re.compile(r'"path"\s+"(?P<path>(?:\\.|[^"\\])*)"')
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


def read_locale_payload(locale_cok: Path, *, locale: str) -> bytes:
    try:
        with zipfile.ZipFile(locale_cok) as archive:
            target = f"{locale}.loc".lower()
            for info in archive.infolist():
                if info.filename.lower() == target:
                    if info.compress_size > MAX_LOCALE_COMPRESSED_BYTES:
                        raise ValueError(
                            f"Locale.cok compressed member size exceeds limit: {info.compress_size} bytes"
                        )
                    if info.file_size > MAX_LOCALE_PAYLOAD_BYTES:
                        raise ValueError(
                            f"Locale.cok uncompressed member size exceeds limit: {info.file_size} bytes"
                        )
                    return archive.read(info)
            return b""
    except zipfile.BadZipFile:
        size = locale_cok.stat().st_size
        if size > MAX_LOCALE_PAYLOAD_BYTES:
            raise ValueError(f"Locale.cok raw file size exceeds limit: {size} bytes")
        return locale_cok.read_bytes()


def _display_token(value: str) -> str:
    token = value.rsplit("/", 1)[-1]
    if "/" in value:
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
            if section_match.group("kind") == "TITLE":
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
        entries = _read_jsonl(entries_path)
        chunks = _read_jsonl(chunks_path)
    except Exception:
        return False
    cached = manifest.get("fingerprint")
    if cached != fingerprint:
        return False
    if len(entries) != manifest.get("entry_count") or len(chunks) != manifest.get("chunk_count"):
        return False
    return _valid_cached_entries(entries) and _valid_cached_chunks(chunks)


def _has_string_fields(row: JSON, fields: List[str]) -> bool:
    return all(isinstance(row.get(field), str) for field in fields)


def _has_nonempty_string_fields(row: JSON, fields: List[str]) -> bool:
    return all(isinstance(row.get(field), str) and bool(str(row.get(field)).strip()) for field in fields)


def _valid_cached_entries(entries: List[JSON]) -> bool:
    required = [
        "entry_id",
        "source",
        "source_key",
        "title",
        "tab",
        "category",
        "raw_content",
        "text",
        "locale",
    ]
    return all(
        isinstance(entry, dict)
        and _has_string_fields(entry, required)
        and _has_nonempty_string_fields(entry, ["entry_id"])
        and entry.get("source") == "game_encyclopedia"
        and isinstance(entry.get("metadata"), dict)
        for entry in entries
    )


def _valid_cached_chunks(chunks: List[JSON]) -> bool:
    required = [
        "chunk_id",
        "entry_id",
        "source",
        "title",
        "tab",
        "category",
        "text",
        "locale",
    ]
    return all(
        isinstance(chunk, dict)
        and _has_string_fields(chunk, required)
        and _has_nonempty_string_fields(chunk, ["chunk_id", "entry_id"])
        and chunk.get("source") == "game_encyclopedia"
        and isinstance(chunk.get("metadata"), dict)
        for chunk in chunks
    )


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
    _manifest_path(cache_dir).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_cached_entries(cache_dir: Path) -> List[JSON]:
    return _read_jsonl(cache_dir / "entries.jsonl")


def load_cached_chunks(cache_dir: Path) -> List[JSON]:
    return _read_jsonl(cache_dir / "chunks.jsonl")


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

        try:
            data = read_locale_payload(discovery.locale_cok_path, locale=config.locale)
            records = extract_glossary_records(data)
            entries = records_to_entries(records, locale=config.locale, source_metadata=_source_metadata(discovery))
            chunks = entries_to_chunks(entries)
            write_cache(cache_dir, fingerprint, entries, chunks=chunks)
            return cls(discovery=discovery, cache_status="rebuilt", entries=entries, chunks=chunks)
        except Exception as exc:
            error_discovery = LocaleDiscovery(
                available=True,
                locale_cok_path=discovery.locale_cok_path,
                game_dir=discovery.game_dir,
                source_kind=discovery.source_kind,
                steam_app_id=discovery.steam_app_id,
                steam_build_id=discovery.steam_build_id,
                warning=str(exc),
            )
            return cls(discovery=error_discovery, cache_status="error", entries=[], chunks=[])

    def status(self) -> JSON:
        payload = source_status_payload(self.discovery, cache_status=self.cache_status, entry_count=len(self.entries))
        payload["available"] = self.available
        if self.cache_status == "error":
            payload["error"] = self.discovery.warning
            payload["warning"] = self.discovery.warning
        if not self.available and not payload.get("warning"):
            payload["warning"] = "Game encyclopedia was found, but no glossary entries could be loaded."
        return payload

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


def source_status_payload(
    discovery: LocaleDiscovery,
    *,
    cache_status: str,
    entry_count: int,
) -> JSON:
    return {
        "source": "game_encyclopedia",
        "available": discovery.available,
        "warning": "" if discovery.available else discovery.warning,
        "source_kind": discovery.source_kind,
        "locale_cok_path": str(discovery.locale_cok_path or ""),
        "game_dir": str(discovery.game_dir or ""),
        "steam_app_id": discovery.steam_app_id or "",
        "steam_build_id": discovery.steam_build_id or "",
        "cache_status": cache_status,
        "entry_count": entry_count,
    }
