#!/usr/bin/env python3
"""
Audit Google Drive files to help with folder reorganization.
- Lists all files in root folder and subfolders
- Identifies duplicates by MD5 checksum (or name/size fallback)
- Finds unique files in each location
- Generates a reorganization checklist
- Read-only operations only
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys

# Force UTF-8 encoding for Windows compatibility with emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from . import config_loader as cfg
else:
    try:
        from . import config_loader as cfg  # python -m scripts.audit_drive_files
    except ModuleNotFoundError:
        import config_loader as cfg  # python scripts/audit_drive_files.py

# Google auth/client - READ ONLY
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


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


@dataclass
class DriveFile:
    id: str
    name: str
    mime: str
    size: str = "0"
    parent_id: str = ""
    parent_name: str = ""
    md5: str = ""
    modified: str = ""

    @property
    def size_mb(self) -> float:
        return int(self.size) / (1024 * 1024) if self.size else 0


def allowed_mimes(include_images: bool) -> Set[str]:
    """Get allowed MIME types based on configuration"""
    mimes = {"application/pdf"}
    if include_images:
        mimes |= {"image/png", "image/jpeg", "image/webp", "image/gif", "image/tiff", "image/heic", "image/heif"}
    return mimes


@dataclass
class FolderInfo:
    id: str
    name: str
    files: List[DriveFile] = field(default_factory=list)
    subfolders: Dict[str, FolderInfo] = field(default_factory=dict)


def get_folder_name(service, folder_id: str) -> str:
    """Get folder name from ID"""
    try:
        result: Dict[str, Any] = service.files().get(fileId=folder_id, fields="name").execute()
        return str(result.get("name", "Unknown"))
    except Exception:
        return "Root"


def list_all_files(service, folder_id: str, folder_name: Optional[str] = None) -> FolderInfo:
    """Recursively list all files and folders"""
    if not folder_name:
        folder_name = get_folder_name(service, folder_id)

    folder_info = FolderInfo(id=folder_id, name=folder_name)

    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id,name,mimeType,size,parents,md5Checksum,modifiedTime)",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )

        for f in resp.get("files", []):
            if f["mimeType"] == "application/vnd.google-apps.folder":
                # Recursively process subfolder
                subfolder = list_all_files(service, f["id"], f["name"])
                folder_info.subfolders[f["name"]] = subfolder
            else:
                # Add file to current folder
                file_obj = DriveFile(
                    id=f["id"],
                    name=f["name"],
                    mime=f["mimeType"],
                    size=f.get("size", "0"),
                    parent_id=folder_id,
                    parent_name=folder_name,
                    md5=f.get("md5Checksum", ""),
                    modified=f.get("modifiedTime", ""),
                )
                folder_info.files.append(file_obj)

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return folder_info


def find_duplicates(folder_info: FolderInfo, include_images: bool = False) -> Dict[str, List[DriveFile]]:
    """Find duplicate files by MD5 checksum (or name/size fallback)"""
    all_files = []

    # Allowed MIME types
    allowed_types = allowed_mimes(include_images)

    def collect_files(folder: FolderInfo, path: str = ""):
        current_path = f"{path}/{folder.name}" if path else folder.name
        for f in folder.files:
            if f.mime in allowed_types:
                f.parent_name = current_path  # Update with full path
                all_files.append(f)
        for subfolder in folder.subfolders.values():
            collect_files(subfolder, current_path)

    collect_files(folder_info)

    # Group by MD5 (preferred) or name+size (fallback)
    duplicates = defaultdict(list)
    for f in all_files:
        # Use MD5 if available, otherwise fall back to name|size
        key = f.md5 or f"{f.name}|{f.size}"
        duplicates[key].append(f)

    # Return only actual duplicates
    return {k: v for k, v in duplicates.items() if len(v) > 1}


def _flatten_files(folder: FolderInfo, allowed_types: Set[str]) -> List[DriveFile]:
    """Recursively collect all files from a folder and its subfolders"""
    out: List[DriveFile] = []
    for f in folder.files:
        if f.mime in allowed_types:
            out.append(f)
    for sub in folder.subfolders.values():
        out.extend(_flatten_files(sub, allowed_types))
    return out


def find_unique_files(
    folder_info: FolderInfo, child_name: str, include_images: bool = False
) -> Tuple[List[DriveFile], List[DriveFile], bool]:
    """Find files unique to root vs specified child subfolder using MD5/content comparison"""
    allowed_types = allowed_mimes(include_images)

    # Root: immediate files only (that's what needs cleaning)
    root_map: Dict[str, DriveFile] = {}
    for f in folder_info.files:
        if f.mime in allowed_types:
            key = f.md5 or f"{f.name}|{f.size}"
            root_map[key] = f

    # Resolve child folder by case-insensitive name
    child_folder = None
    for name, sub in folder_info.subfolders.items():
        if name.lower() == child_name.lower():
            child_folder = sub
            break

    # Child: recurse (Public can have subfolders)
    child_map: Dict[str, DriveFile] = {}
    child_found = child_folder is not None
    if child_folder:
        for f in _flatten_files(child_folder, allowed_types):
            key = f.md5 or f"{f.name}|{f.size}"
            child_map[key] = f

    # Unique by content key
    root_only = [f for k, f in root_map.items() if k not in child_map]
    child_only = [f for k, f in child_map.items() if k not in root_map]
    return root_only, child_only, child_found


def generate_mapping_file(folder_info: FolderInfo, output_path: Path, include_images: bool = False):
    """Generate a mapping file for renaming checklist"""
    # Allowed MIME types
    allowed_types = allowed_mimes(include_images)

    files: List[Dict[str, Any]] = []
    mapping: Dict[str, Any] = {
        "_description": "File inventory for reorganization. Use as a checklist for renaming in Drive UI.",
        "_instructions": [
            "1. Review this inventory to plan your file organization",
            "2. Rename/move files directly in Google Drive",
            "3. Run 'make drive-apply' to update the site with new IDs",
            "4. This is READ-ONLY - no automated renaming",
        ],
        "files": files,
    }

    def add_files(folder: FolderInfo, path: str = ""):
        current_path = f"{path}/{folder.name}" if path else folder.name
        for f in folder.files:
            if f.mime in allowed_types:
                files.append(
                    {
                        "id": f.id,
                        "current_name": f.name,
                        "new_name": f.name,  # Use as checklist
                        "size_mb": round(f.size_mb, 2),
                        "location": current_path,
                        "modified": f.modified[:10] if f.modified else "",
                        "mime_type": f.mime,
                        "md5": f.md5[:8] if f.md5 else "",  # First 8 chars for readability
                    }
                )
        for subfolder in folder.subfolders.values():
            add_files(subfolder, current_path)

    add_files(folder_info)

    # Sort by location and name
    files.sort(key=lambda x: (x["location"], x["current_name"]))

    output_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    return mapping


def write_csv(mapping: dict, csv_path: Path):
    """Write mapping to CSV for easier spreadsheet editing"""
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["id", "current_name", "new_name", "size_mb", "location", "modified", "mime_type", "md5"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in mapping["files"]:
            writer.writerow(row)


def _count_files_recursive(folder: FolderInfo, allowed_types: Set[str]) -> int:
    """Recursively count files matching allowed types"""
    count = sum(1 for f in folder.files if f.mime in allowed_types)
    for sub in folder.subfolders.values():
        count += _count_files_recursive(sub, allowed_types)
    return count


def print_audit_report(
    folder_info: FolderInfo, duplicates: Dict, root_only: List, child_only: List, child_name: str, include_images: bool
):
    """Print detailed audit report"""
    print("\n" + "=" * 60)
    print("GOOGLE DRIVE AUDIT REPORT")
    print("=" * 60)

    # Summary
    allowed_types = allowed_mimes(include_images)
    total_files = _count_files_recursive(folder_info, allowed_types)
    print(f"\nTotal files found: {total_files}")
    print(f"Subfolders: {len(folder_info.subfolders)}")
    print(f"Comparing: Root vs '{child_name}' subfolder")

    # Duplicates
    if duplicates:
        print(f"\n📋 DUPLICATES FOUND: {len(duplicates)} sets")
        print("-" * 40)
        for i, (key, files) in enumerate(duplicates.items(), 1):
            # Show filename from first duplicate
            name = files[0].name
            if key.startswith(name):
                # It's using name|size key
                print(f"\n{i}. {name} (by name+size)")
            else:
                # It's using MD5 key
                print(f"\n{i}. {name} (MD5: {key[:8]}...)")
            for f in files:
                print(f"   - {f.parent_name}/{f.name} ({f.size_mb:.1f} MB)")

    # Unique to root
    if root_only:
        print(f"\n⚠️  FILES ONLY IN ROOT: {len(root_only)}")
        print("-" * 40)
        for f in root_only:
            print(f"  - {f.name} ({f.size_mb:.1f} MB)")

    # Unique to child folder
    if child_only:
        print(f"\n✅ FILES ONLY IN '{child_name.upper()}': {len(child_only)}")
        print("-" * 40)
        for f in child_only:
            print(f"  - {f.name} ({f.size_mb:.1f} MB)")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("-" * 40)

    if duplicates:
        print(f"1. Remove duplicate files from root (keep copies in '{child_name}')")
    if root_only:
        print(f"2. Review root-only files - copy needed ones to '{child_name}' folder")
    print("3. Use file-mapping.json/csv as a checklist for renaming")
    print("4. Rename files directly in Google Drive UI")
    print("5. Run 'make drive-apply' after organizing")

    print("\n")


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Audit Google Drive files (read-only)")
    parser.add_argument("--folder", default=None, help="Drive folder ID to audit (defaults to config)")
    parser.add_argument("--child", default="Public", help="Child subfolder name to compare against (default: Public)")
    parser.add_argument("--include-images", action="store_true", help="Include images in the inventory")
    parser.add_argument("--csv", dest="csv_out", help="Also write a CSV file (e.g., file-mapping.csv)")
    parser.add_argument("--output", default="file-mapping.json", help="Output JSON mapping file name")
    args = parser.parse_args()

    # Get folder ID from args or config
    folder_id = args.folder or cfg.public_folder_id()
    if not folder_id:
        sys.exit("No folder ID. Set PUBLIC_FOLDER_ID in .env or config/settings.json, or pass --folder.")

    # Show where folder ID came from for traceability
    if args.folder:
        print(f"Using folder ID from command line: {folder_id}")
    else:
        print(f"Using folder ID from config: {folder_id}")

    print("Authenticating with Google (read-only)...")
    service = _google_client()

    print("Scanning Drive folder...")
    folder_info = list_all_files(service, folder_id)

    print(f'Analyzing files (comparing root vs "{args.child}")...')
    duplicates = find_duplicates(folder_info, include_images=args.include_images)
    root_only, child_only, child_found = find_unique_files(folder_info, args.child, include_images=args.include_images)

    if not child_found:
        print(f"\n⚠️  Subfolder '{args.child}' not found under '{folder_info.name}'. Treating child as empty.")

    # Generate mapping file
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping = generate_mapping_file(folder_info, output_path, include_images=args.include_images)
    print(f"\n📝 File inventory saved to: {output_path}")
    print(f"   Total files mapped: {len(mapping['files'])}")

    # Write CSV if requested
    if args.csv_out:
        csv_path = root / args.csv_out
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(mapping, csv_path)
        print(f"📊 CSV inventory saved to: {csv_path}")

    # Print report
    print_audit_report(folder_info, duplicates, root_only, child_only, args.child, args.include_images)

    print("Next steps:")
    print(f"1. Create a '{args.child}' subfolder in Google Drive (if not exists)")
    print("2. Move/copy needed files from root to this subfolder")
    print("3. Remove duplicates from root")
    print("4. Rename files as needed in Drive UI")
    print("5. Run 'make drive-apply SITE=lancaster-12' to update site")


if __name__ == "__main__":
    try:
        import importlib.util

        if importlib.util.find_spec("google.auth") is None:
            raise ImportError("google.auth not found")
    except ImportError:
        print("ERROR: Google API libraries not installed!")
        print("\nRun: make deps")
        print("Or: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    main()
