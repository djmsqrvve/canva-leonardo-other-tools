"""Firefox profile discovery and session sync."""
from __future__ import annotations

import configparser
import shutil
from pathlib import Path

DEFAULT_SOURCE_ROOTS = (
    Path.home() / "snap/firefox/common/.mozilla/firefox",
    Path.home() / ".mozilla/firefox",
)

SESSION_FILES = (
    "cookies.sqlite",
    "cookies.sqlite-wal",
    "webappsstore.sqlite",
    "webappsstore.sqlite-wal",
    "formhistory.sqlite",
    "permissions.sqlite",
    "cert9.db",
    "key4.db",
    "logins.db",
    "pkcs11.txt",
    "prefs.js",
    "sessionstore.jsonlz4",
    "containers.json",
)

LOCK_FILES = ("lock", ".parentlock")


def find_default_source_profile() -> Path | None:
    """Walk known Firefox install roots and return the default profile path."""
    for base in DEFAULT_SOURCE_ROOTS:
        if not base.is_dir():
            continue
        profiles_ini = base / "profiles.ini"
        if profiles_ini.exists():
            config = configparser.ConfigParser()
            config.read(profiles_ini)
            for section in config.sections():
                if config.get(section, "Default", fallback="") == "1" or config.get(
                    section, "Name", fallback=""
                ).lower() in ("default", "default-release"):
                    rel_path = config.get(section, "Path", fallback="")
                    if rel_path:
                        candidate = base / rel_path
                        if candidate.is_dir():
                            return candidate
        for entry in sorted(base.iterdir()):
            if entry.is_dir() and "default" in entry.name.lower():
                return entry
    return None


def sync_session(source: Path, target: Path, *, include_storage: bool = True) -> int:
    """Copy session-critical files from *source* profile to *target*.

    Returns the number of items copied.
    """
    if source == target:
        return 0
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for filename in SESSION_FILES:
        src = source / filename
        if src.exists():
            shutil.copy2(src, target / filename)
            copied += 1
    if include_storage:
        storage_src = source / "storage"
        storage_dst = target / "storage"
        if storage_src.is_dir():
            if storage_dst.exists():
                shutil.rmtree(storage_dst)
            shutil.copytree(storage_src, storage_dst, dirs_exist_ok=True)
            copied += 1
    return copied


def remove_lock_files(profile: Path) -> None:
    """Remove Firefox lock files so a second instance can use the profile."""
    for name in LOCK_FILES:
        p = profile / name
        if p.exists() or p.is_symlink():
            p.unlink()
