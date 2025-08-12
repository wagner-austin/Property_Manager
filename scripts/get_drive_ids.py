#!/usr/bin/env python3
"""
Fetch Google Drive PDF IDs for a property folder and write them into sites/<slug>/data.json.
- Auth: credentials.json (OAuth desktop) + token.json (cached)
- Recursively scans folder for PDFs
- Heuristically matches files to presentation/docs/plans/lots
- Backs up data.json, then writes real IDs into the "file" fields
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

if TYPE_CHECKING:
    from . import config_loader as cfg
else:
    try:
        from . import config_loader as cfg  # python -m scripts.get_drive_ids
    except ModuleNotFoundError:
        import config_loader as cfg  # python scripts/get_drive_ids.py

# --- Google auth/client ---
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
VERBOSE = False  # Global flag for verbose output


def _google_client():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    cred_path, token_path = cfg.credentials_paths()
    if not cred_path.exists():
        sys.exit(f"credentials.json not found at {cred_path}. Run setup-drive-api.py first.")

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds, cache_discovery=False)


# --- Helpers ---
def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\.(pdf|docx?)$", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def has_all(name: str, *tokens: str) -> bool:
    n = norm(name)
    return all(t in n for t in tokens)


@dataclass
class GFile:
    id: str
    name: str
    mime: str
    view: Optional[str]


# --- Drive listing (recursive) ---
def list_pdfs(service, folder_id: str) -> List[GFile]:
    pdfs: List[GFile] = []
    folders = [folder_id]
    while folders:
        parent = folders.pop()
        page_token = None
        while True:
            resp = (
                service.files()
                .list(
                    q=f"'{parent}' in parents and trashed=false",
                    fields="nextPageToken, files(id,name,mimeType,webViewLink)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )
            for f in resp.get("files", []):
                if f["mimeType"] == "application/pdf":
                    pdfs.append(GFile(f["id"], f["name"], f["mimeType"], f.get("webViewLink")))
                elif f["mimeType"] == "application/vnd.google-apps.folder":
                    folders.append(f["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    # Dedup by filename, keep the longest name (usually the "real" one)
    by_name: Dict[str, GFile] = {}
    for f in pdfs:
        k = f.name.lower()
        if k not in by_name or len(f.name) > len(by_name[k].name):
            by_name[k] = f
    return sorted(by_name.values(), key=lambda x: x.name.lower())


# --- Matching rules ---
def score_match(target: str, fname: str) -> int:
    """Simple token scoring, higher is better"""
    t = norm(target)
    n = norm(fname)
    score = 0

    # Log for debugging
    if VERBOSE:
        print(f"    Matching '{target}' against '{fname}'")
        print(f"      Normalized: '{t}' vs '{n}'")

    for tok in t.split():
        if tok in n:
            score += 2

    # Special handling for presentation files
    if "presentation" in t and "presentation" in n:
        score += 10

    # Improved plan matching - look for "plan X" pattern
    m_plan = re.search(r"\bplan\s*(\d+)\b", t)
    if m_plan:
        plan_num = m_plan.group(1)
        # More flexible pattern - allow words between "plan" and number
        if re.search(rf"\bplan\b.*\b{plan_num}\b", n):
            score += 10
            if VERBOSE:
                print(f"      Found Plan {plan_num} match! Score: {score}")

    # Lot matching
    m_lot = re.search(r"\blot\s*(\d+)\b", t)
    if m_lot:
        lot_num = m_lot.group(1).lstrip("0")  # Remove leading zeros
        if re.search(rf"\blot[^0-9]*0*{lot_num}\b", n):
            score += 5

    # Tentative / Plat Map (including common misspelling)
    if ("tentative" in t or "tenative" in t or "platmap" in t or ("plat" in t and "map" in t)) and (
        "tentative" in n or "tenative" in n or "platmap" in n or ("plat" in n and "map" in n)
    ):
        score += 5

    # Entitlements matching
    if "entitlement" in t and "entitlement" in n:
        score += 8

    # LLC/Company info matching
    if ("llc" in t or "company" in t) and "llc" in n:
        score += 8

    # Grading plan matching
    if "grading" in t and "grading" in n:
        score += 8

    # Court/Verella matching
    if ("court" in t or "verella" in t) and ("court" in n or "verella" in n):
        score += 8

    if VERBOSE and score > 0:
        print(f"      Final score: {score}")

    return score


def best_file_for(target_title: str, files: List[GFile]) -> Optional[GFile]:
    best: Tuple[int, Optional[GFile]] = (0, None)
    for f in files:
        sc = score_match(target_title, f.name)
        if sc > best[0]:
            best = (sc, f)
    return best[1] if best[0] > 0 else None


# --- Main apply logic ---
def load_site_json(site_path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(site_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError(f"{site_path} must contain a JSON object")
        return cast(Dict[str, Any], data)
    except Exception as e:
        sys.exit(f"Failed to read {site_path}: {e}")


def save_site_json(site_path: Path, data: Dict[str, Any]) -> None:
    backup = site_path.with_suffix(f".bak.{int(time.time())}.json")
    backup.write_text(site_path.read_text(encoding="utf-8"), encoding="utf-8")
    site_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Backup created: {backup.name}")


def get_folder_id(site: Dict[str, Any], cli_folder: Optional[str]) -> str:
    if cli_folder:
        return cli_folder

    # Prefer per-site config first
    for path in [
        ("drive", "publicFolderId"),
        ("contact", "publicFolderId"),
        ("publicFolderId",),
        ("drive", "folderId"),
        ("contact", "folderId"),
        ("folderId",),
    ]:
        cur = site
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and isinstance(cur, str) and cur.strip():
            return cur.strip()

    # Global fallback from settings.json
    cfg_id = cfg.public_folder_id()
    if cfg_id:
        return cfg_id

    sys.exit(
        "No Drive folderId found. Put it in site data.json (drive.publicFolderId), or in config/settings.json (publicFolderId), or pass --folder."
    )


def apply_ids_to_site(site: dict, files: List[GFile]) -> Tuple[int, int, List[str]]:
    """Return (updated_count, total_targets, matched_items)"""
    updated = 0
    total = 0
    matched = []

    def try_set(obj: dict, title_fallback: str):
        nonlocal updated, total
        if not isinstance(obj, dict):
            return
        total += 1
        title = obj.get("title") or title_fallback
        f = best_file_for(title, files)
        if f:
            prev = obj.get("file")
            obj["file"] = f.id  # store just the ID; your app extracts Drive IDs already
            if prev != obj["file"]:
                updated += 1
                matched.append(f"{title} -> {f.name[:40]}...")
            obj.setdefault("name", f.name)  # optional: helpful for debugging/UI
        # else leave as-is

    # Presentation
    if isinstance(site.get("presentation"), dict):
        try_set(site["presentation"], "presentation")

    # Project docs
    for doc in site.get("projectDocs", []) or []:
        try_set(doc, doc.get("title") or "")

    # Plans
    for plan in site.get("plans", []) or []:
        t = plan.get("title") or ""
        try_set(plan, t)

    # Lots
    for lot in site.get("lots", []) or []:
        t = lot.get("number") or lot.get("title") or ""
        try_set(lot, t)

    return updated, total, matched


def main():
    parser = argparse.ArgumentParser(description="Apply Google Drive PDF IDs to site JSON.")
    parser.add_argument("--site", default=None, help="site slug under sites/ (default from config)")
    parser.add_argument("--folder", help="override Drive folder ID (otherwise read from config/site JSON)")
    parser.add_argument("--dry-run", action="store_true", help="list matches but do not write")
    parser.add_argument("-v", "--verbose", action="store_true", help="print matching debug info")
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    # Use config for defaults
    site_slug = args.site or cfg.default_site()
    site_path = cfg.sites_dir() / site_slug / "data.json"
    if not site_path.exists():
        sys.exit(f"Site JSON not found: {site_path}")

    site = load_site_json(site_path)
    folder_id = get_folder_id(site, args.folder)

    print("Authenticating with Google...")
    service = _google_client()

    print(f"Scanning Drive folder {folder_id} (recursively)...")
    files = list_pdfs(service, folder_id)
    print(f"Found {len(files)} PDF(s)")

    # Show what we found
    print("\nPDFs in Drive:")
    for f in files[:10]:  # Show first 10
        print(f"  - {f.name}")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")

    updated, total, matched = apply_ids_to_site(site, files)

    if args.dry_run:
        print(f"\n(DRY RUN) Would update {updated}/{total} targets.")
        if matched:
            print("\nMatches found:")
            for m in matched:
                print(f"  - {m}")
        return

    save_site_json(site_path, site)
    print(f"\nUpdated {updated}/{total} entries in {site_path.name}")

    if matched:
        print("\nMatched:")
        for m in matched[:10]:
            print(f"  - {m}")
        if len(matched) > 10:
            print(f"  ... and {len(matched) - 10} more")

    print("\nRefresh your browser; buttons should be live!")


if __name__ == "__main__":
    # Check for required library
    try:
        import importlib.util

        if importlib.util.find_spec("google.auth") is None:
            raise ImportError("google.auth not found")
    except ImportError:
        print("ERROR: Google API libraries not installed!")
        print("\nRun this command first:")
        print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    main()
