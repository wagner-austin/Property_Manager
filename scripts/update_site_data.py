#!/usr/bin/env python3
"""
Auto-update site data from urls.json
Reads urls.json (after you paste real IDs), fuzzy-matches filenames to known docs,
and updates sites/[site]/data.json with the actual Drive file IDs.
"""

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

# Force UTF-8 encoding for Windows compatibility with emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

if TYPE_CHECKING:
    from . import config_loader as cfg
else:
    try:
        from . import config_loader as cfg  # python -m scripts.update_site_data
    except ModuleNotFoundError:
        import config_loader as cfg  # python scripts/update_site_data.py

ROOT = Path(__file__).resolve().parent.parent
ID_RE = re.compile(r"/d/([-\w]{10,})|[?&]id=([-\w]{10,})")


def extract_id(s: str):
    """Extract Drive file ID from various formats"""
    s = (s or "").strip()
    if not s or s in {"PASTE_FILE_ID_HERE", "FILE_ID_OR_URL"}:
        return None
    if re.fullmatch(r"[-\w]{10,}", s):
        return s
    m = ID_RE.search(s)
    return (m.group(1) or m.group(2)) if m else None


def load_urls(path: Path):
    """Load and normalize urls.json entries"""
    data = json.loads(path.read_text(encoding="utf-8"))

    # Accept either {"files":[...]} or [...]
    rows = data["files"] if isinstance(data, dict) and "files" in data else (data if isinstance(data, list) else [])

    norm = []
    empty_count = 0

    for r in rows:
        if not isinstance(r, dict):
            continue

        # Normalize sources
        filename = (r.get("filename") or r.get("name") or r.get("path") or "").strip()
        id_source = (
            r.get("id")
            or r.get("file_id")
            or r.get("url")
            or r.get("shareUrl")
            or r.get("share_url")
            or r.get("view_url")
            or r.get("preview_url")
            or ""
        )
        id_source = str(id_source).strip()

        file_id = extract_id(id_source)

        if filename and not file_id:
            empty_count += 1
        if not filename:
            # Skip rows with no usable filename
            continue

        norm.append(
            {
                "filename": filename,
                "file_id": file_id,
                "view_url": r.get("view_url") or "",
                "preview_url": r.get("preview_url") or "",
            }
        )

    if empty_count > 0:
        print(f"⚠️  Warning: {empty_count} file(s) in urls.json have no ID. Fill in the 'id' field.")

    return norm


def fid_for(rows, *needles):
    """Find file ID for a document by matching filename keywords"""
    nd = [n.lower() for n in needles]
    for r in rows:
        name = (r["filename"] or "").lower()
        if all(n in name for n in nd):
            return r["file_id"] or extract_id(r["view_url"]) or extract_id(r["preview_url"])
    return None


def apply_to_json(json_path: Path, rows):
    """Apply file IDs from urls.json to site data.json"""
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Map filenames to known documents
    ids = {
        "presentation": fid_for(rows, "presentation"),
        "tentative": fid_for(rows, "tentative", "map") or fid_for(rows, "tenative", "map"),
        "entitlements": fid_for(rows, "entitlements"),
        "grading": fid_for(rows, "grading") or fid_for(rows, "conceptual", "grading"),
        "llc": fid_for(rows, "llc", "info") or fid_for(rows, "43741"),
        "verella": fid_for(rows, "verella"),
        "duke": fid_for(rows, "duke"),
        "plan1": fid_for(rows, "plan", "1"),
        "plan2": fid_for(rows, "plan", "2"),
        "plan3": fid_for(rows, "plan", "3"),
        "plan4": fid_for(rows, "plan", "4") or fid_for(rows, "plan", "#4"),
        "desert": fid_for(rows, "desert", "crest"),
        # Lot-specific docs (if your filenames include "lot 1", etc.)
        "lot1": fid_for(rows, "lot", "1"),
        "lot2": fid_for(rows, "lot", "2"),
        "lot3": fid_for(rows, "lot", "3"),
        "lot4": fid_for(rows, "lot", "4"),
        "lot5": fid_for(rows, "lot", "5"),
        "lot6": fid_for(rows, "lot", "6"),
        "lot7": fid_for(rows, "lot", "7"),
        "lot8": fid_for(rows, "lot", "8"),
        "lot9": fid_for(rows, "lot", "9"),
        "lot10": fid_for(rows, "lot", "10"),
        "lot11": fid_for(rows, "lot", "11"),
        "lot12": fid_for(rows, "lot", "12"),
    }

    # Helper to set first match by title
    def set_by_title(items, title, fid):
        if not (items and fid):
            return False
        for it in items:
            if it.get("title") == title:
                it["file"] = fid
                return True
        return False

    changed = 0

    # Update presentation
    if "presentation" in data and ids["presentation"]:
        data["presentation"]["file"] = ids["presentation"]
        changed += 1

    # Update project documents by title
    changed += set_by_title(data.get("projectDocs"), "Tentative Map", ids["tentative"]) or 0
    changed += set_by_title(data.get("projectDocs"), "Entitlements", ids["entitlements"]) or 0
    changed += set_by_title(data.get("projectDocs"), "Grading Plan", ids["grading"]) or 0
    changed += set_by_title(data.get("projectDocs"), "LLC Information", ids["llc"]) or 0
    changed += set_by_title(data.get("projectDocs"), "Verella Court", ids["verella"]) or 0
    changed += set_by_title(data.get("projectDocs"), "Duke Development", ids["duke"]) or 0

    # Update plans by title
    changed += set_by_title(data.get("plans"), "Plan 1", ids["plan1"]) or 0
    changed += set_by_title(data.get("plans"), "Plan 2", ids["plan2"]) or 0
    changed += set_by_title(data.get("plans"), "Plan 3", ids["plan3"]) or 0
    changed += set_by_title(data.get("plans"), "Plan 4", ids["plan4"]) or 0
    changed += set_by_title(data.get("plans"), "Desert Crest Plan", ids["desert"]) or 0

    # Update lots (if they have individual PDFs)
    if "lots" in data:
        for i in range(1, 13):
            lot_id = ids[f"lot{i}"]
            if lot_id:
                for lot in data["lots"]:
                    if lot.get("number") == i or lot.get("title") == f"Lot {i}":
                        lot["file"] = lot_id
                        changed += 1
                        break

    # Create backup and write updated file
    backup = json_path.with_suffix(f".bak.{int(time.time())}.json")
    backup.write_text(json.dumps(data, indent=2), encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return ids, changed


def main():
    ap = argparse.ArgumentParser(description="Update site data from urls.json")
    ap.add_argument("--site", default=None, help="site slug under sites/ (default from config)")
    ap.add_argument("--urls", default=str(ROOT / "urls.json"), help="path to urls.json")
    args = ap.parse_args()

    # Use config for default site
    site_slug = args.site or cfg.default_site()

    urls_path = Path(args.urls)
    if not urls_path.exists():
        sys.exit("Error: urls.json not found. Run generate_url_template.py first.")

    rows = load_urls(urls_path)
    json_path = cfg.sites_dir() / site_slug / "data.json"
    if not json_path.exists():
        # Try to create the site directory and use template if available
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # Prefer the shared template; fall back to lancaster-12 if needed
        template = cfg.sites_dir() / "_template" / "data.json"
        if not template.exists():
            alt = cfg.sites_dir() / "lancaster-12" / "data.json"
            if alt.exists():
                template = alt

        if template.exists() and template.resolve() != json_path.resolve():
            import shutil

            shutil.copy(template, json_path)
            print(f"Seeded {json_path} from {template}")
        else:
            sys.exit(f"Error: {json_path} not found and no template available.")

    ids, changed = apply_to_json(json_path, rows)

    # Summary
    found = sum(1 for v in ids.values() if v)
    total = len(ids)
    print(f"Updated {changed} entries in {site_slug}/data.json")
    print(f"Matched {found}/{total} known documents")

    # Show what was matched
    if found > 0:
        print("\nMatched documents:")
        for k, v in ids.items():
            if v:
                print(f"  - {k}: {v[:20]}...")

    # Check for remaining placeholders
    data_text = json_path.read_text(encoding="utf-8")
    missing_placeholders = data_text.count("FILE_ID_OR_URL")
    if missing_placeholders:
        print(f"\nWARNING: {missing_placeholders} placeholders still remain")
        print("   (lots/plans/docs without matches in urls.json)")
    else:
        print("\nAll placeholders replaced! Site is ready.")


if __name__ == "__main__":
    main()
