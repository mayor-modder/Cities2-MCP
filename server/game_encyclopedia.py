from __future__ import annotations

import json
import os
import re
import sys
import time
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
    return len(entries) == manifest.get("entry_count") and len(chunks) == manifest.get("chunk_count")


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
