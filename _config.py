"""Config loader for ref-downloader.

Resolution order (highest priority last — later overrides earlier):
    1. config.example.toml (committed defaults)
    2. config.local.toml (gitignored, user-specific)
    3. REF_DOWNLOADER_CONFIG env var (path to alternate TOML)
    4. explicit_path arg (typically from --config CLI)
    5. Per-field env vars (REF_DOWNLOADER_MAILTO, _ZOTERO_DB, _EDGE_PROFILE, _DISABLE_EXTENSIONS)

Used by run_ref_downloader.py, extract_refs.py, validate_refs.py, download_refs.py.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore

PACKAGE_DIR = Path(__file__).resolve().parent
EXAMPLE_TOML = PACKAGE_DIR / "config.example.toml"
LOCAL_TOML = PACKAGE_DIR / "config.local.toml"
PLACEHOLDER_MAILTO = "your.email@example.com"


@dataclass
class CrossrefConfig:
    mailto: str = PLACEHOLDER_MAILTO


@dataclass
class ZoteroConfig:
    db_path: str = ""


@dataclass
class BrowserConfig:
    edge_profile_dir: str = ""
    disable_extensions: bool = False


@dataclass
class InstitutionConfig:
    auth_hosts: List[str] = field(default_factory=list)
    auth_url_fragments: List[str] = field(default_factory=list)
    auth_page_titles: List[str] = field(default_factory=list)
    auth_loading_titles: List[str] = field(default_factory=list)
    ignored_access_dois: List[str] = field(default_factory=list)


@dataclass
class Config:
    crossref: CrossrefConfig = field(default_factory=CrossrefConfig)
    zotero: ZoteroConfig = field(default_factory=ZoteroConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    institution: InstitutionConfig = field(default_factory=InstitutionConfig)
    source_files: List[str] = field(default_factory=list)


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _merge_dict(base: dict, overlay: dict) -> dict:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _merge_dict(dict(base[key]), value)
        else:
            base[key] = value
    return base


def _build_from_dict(data: dict, source_files: List[str]) -> Config:
    crossref = data.get("crossref", {}) or {}
    zotero = data.get("zotero", {}) or {}
    browser = data.get("browser", {}) or {}
    institution = data.get("institution", {}) or {}
    return Config(
        crossref=CrossrefConfig(
            mailto=str(crossref.get("mailto", PLACEHOLDER_MAILTO)),
        ),
        zotero=ZoteroConfig(
            db_path=str(zotero.get("db_path", "")),
        ),
        browser=BrowserConfig(
            edge_profile_dir=str(browser.get("edge_profile_dir", "")),
            disable_extensions=bool(browser.get("disable_extensions", False)),
        ),
        institution=InstitutionConfig(
            auth_hosts=list(institution.get("auth_hosts", []) or []),
            auth_url_fragments=list(institution.get("auth_url_fragments", []) or []),
            auth_page_titles=list(institution.get("auth_page_titles", []) or []),
            auth_loading_titles=list(institution.get("auth_loading_titles", []) or []),
            ignored_access_dois=list(institution.get("ignored_access_dois", []) or []),
        ),
        source_files=source_files,
    )


def _apply_env_overrides(cfg: Config) -> Config:
    mailto = os.environ.get("REF_DOWNLOADER_MAILTO")
    zotero = os.environ.get("REF_DOWNLOADER_ZOTERO_DB")
    edge = os.environ.get("REF_DOWNLOADER_EDGE_PROFILE")
    disable_ext = os.environ.get("REF_DOWNLOADER_DISABLE_EXTENSIONS")

    if mailto:
        cfg = replace(cfg, crossref=replace(cfg.crossref, mailto=mailto))
    if zotero is not None:
        cfg = replace(cfg, zotero=replace(cfg.zotero, db_path=zotero))
    if edge is not None:
        cfg = replace(cfg, browser=replace(cfg.browser, edge_profile_dir=edge))
    if disable_ext is not None:
        flag = disable_ext.strip().lower() in ("1", "true", "yes", "on")
        cfg = replace(cfg, browser=replace(cfg.browser, disable_extensions=flag))
    return cfg


def load_config(explicit_path: Optional[Path] = None) -> Config:
    """Load config from TOML files + env vars; return a Config dataclass.

    explicit_path: if provided (e.g. from --config CLI arg), takes priority over
    REF_DOWNLOADER_CONFIG env var, which takes priority over config.local.toml.
    """
    chain: List[Path] = []
    chain.append(EXAMPLE_TOML)
    if LOCAL_TOML.exists():
        chain.append(LOCAL_TOML)

    env_path = os.environ.get("REF_DOWNLOADER_CONFIG")
    if env_path:
        chain.append(Path(env_path).expanduser())
    if explicit_path:
        chain.append(explicit_path.expanduser())

    merged: dict = {}
    used: List[str] = []
    for path in chain:
        if not path.exists():
            continue
        data = _load_toml(path)
        merged = _merge_dict(merged, data)
        used.append(str(path))

    cfg = _build_from_dict(merged, used)
    cfg = _apply_env_overrides(cfg)
    return cfg


def user_agent_from(cfg: Config, app: str = "RefDownloader/1.0") -> str:
    return f"{app} (mailto:{cfg.crossref.mailto})"


def warn_if_placeholder_mailto(cfg: Config) -> None:
    if cfg.crossref.mailto == PLACEHOLDER_MAILTO:
        print(
            "WARNING: crossref.mailto is the placeholder. "
            "Edit config.local.toml (copy from config.example.toml) or set "
            "REF_DOWNLOADER_MAILTO to enter the Crossref polite pool.",
            file=sys.stderr,
        )
