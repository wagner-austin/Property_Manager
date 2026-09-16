#!/usr/bin/env python3
"""Check that sites/index.json lists exactly the property sites on disk.

The page builds its property tabs from sites/index.json, and a static host
cannot list a directory, so the manifest is the only way a visitor finds a
site. A site folder missing from the manifest is unreachable from the tabs;
a manifest entry with no folder is a tab that fails to load. Both are
reported, and the script exits non-zero if either exists.

Each entry's status is "live" (a tab on the public site) or "preview" (a tab
only at /preview, for review before it goes public).

Usage:
    python -m scripts.check_site_index
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, TypedDict

SITES_DIR = Path("sites")
INDEX_NAME = "sites/index.json"
INDEX_PATH = Path(INDEX_NAME)
IGNORED_DIRS = frozenset({"_template"})
STATUSES = ("live", "preview")


class SiteEntry(TypedDict):
    """One tab in the manifest."""

    slug: str
    label: str
    status: str


def require_str(obj: dict, key: str, where: str) -> str:
    """Return obj[key] as a non-empty string.

    Args:
        obj: The decoded JSON object.
        key: The field to read.
        where: A location label for the error message.

    Returns:
        str: The field's value.

    Raises:
        ValueError: If the field is missing, not a string, or blank.
    """
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: '{key}' must be a non-empty string")
    return value


def decode_index(raw: object) -> List[SiteEntry]:
    """Decode the manifest into typed entries.

    Args:
        raw: The result of json.loads on sites/index.json.

    Returns:
        list[SiteEntry]: The entries in tab order.

    Raises:
        ValueError: If the shape is wrong, a slug repeats, a status is not
            one of STATUSES, or no entry is live.
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("sites"), list):
        raise ValueError(f"{INDEX_NAME}: expected an object with a 'sites' array")
    entries: List[SiteEntry] = []
    seen: set = set()
    for i, item in enumerate(raw["sites"]):
        where = f"{INDEX_NAME} sites[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where}: expected an object")
        slug = require_str(item, "slug", where)
        if slug in seen:
            raise ValueError(f"{where}: slug '{slug}' is listed twice")
        seen.add(slug)
        status = require_str(item, "status", where)
        if status not in STATUSES:
            raise ValueError(f"{where}: status '{status}' must be one of {', '.join(STATUSES)}")
        entries.append(SiteEntry(slug=slug, label=require_str(item, "label", where), status=status))
    # The public site opens the first live entry's page by default.
    if not any(e["status"] == "live" for e in entries):
        raise ValueError(f"{INDEX_NAME}: at least one site must be live")
    return entries


def find_problems(entries: List[SiteEntry], site_dirs: List[str]) -> List[str]:
    """Compare the manifest against the site folders in both directions.

    Args:
        entries: The decoded manifest.
        site_dirs: Names of the folders under sites/ that hold a data.json.

    Returns:
        list[str]: One message per mismatch; empty when they agree.
    """
    listed = [e["slug"] for e in entries]
    problems = [
        f"sites/{slug}/data.json is missing, but {INDEX_NAME} lists '{slug}'"
        for slug in listed
        if slug not in site_dirs
    ]
    problems += [
        f"sites/{name}/ exists but is not in {INDEX_NAME}, so no tab reaches it"
        for name in site_dirs
        if name not in listed
    ]
    return problems


def main() -> int:
    """Run the check and print the result.

    Returns:
        int: 0 when the manifest matches the folders, 1 otherwise.
    """
    entries = decode_index(json.loads(INDEX_PATH.read_text(encoding="utf-8")))
    candidates = [p for p in SITES_DIR.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS]
    site_dirs = sorted(p.name for p in candidates if (p / "data.json").is_file())
    problems = find_problems(entries, site_dirs)
    # ASCII only: the Windows console codepage cannot encode emoji.
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print(f"OK: {INDEX_NAME} lists all {len(entries)} sites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
