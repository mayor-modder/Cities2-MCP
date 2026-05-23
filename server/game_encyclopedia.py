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
        "warning": "" if discovery.available else discovery.warning,
        "source_kind": discovery.source_kind,
        "locale_cok_path": str(discovery.locale_cok_path or ""),
        "game_dir": str(discovery.game_dir or ""),
        "steam_app_id": discovery.steam_app_id or "",
        "steam_build_id": discovery.steam_build_id or "",
        "cache_status": cache_status,
        "entry_count": entry_count,
    }
