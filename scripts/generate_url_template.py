#!/usr/bin/env python3
"""
Generate a URL/ID mapping template for PDFs in your public folder.

- Reads defaults from config (.env / config/settings.json)
- Can be overridden with CLI flags
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import config_loader as cfg
else:
    try:
        from . import config_loader as cfg  # python -m scripts.generate_url_template
    except ModuleNotFoundError:
        import config_loader as cfg  # python scripts/generate_url_template.py


ROOT = Path(__file__).resolve().parent.parent


def _find_pdfs(root: Path):
    return sorted(root.rglob("*.pdf"), key=lambda p: p.name.lower())


def _dedupe_keep_largest(paths):
    """Deduplicate by filename, keep largest file per name."""
    by_name = {}
    for p in paths:
        cur = by_name.get(p.name)
        if cur is None or p.stat().st_size > cur.stat().st_size:
            by_name[p.name] = p
    return [by_name[k] for k in sorted(by_name.keys(), key=str.lower)]


def main():
    ap = argparse.ArgumentParser(description="Generate a mapping template of PDFs in the public folder.")
    ap.add_argument(
        "-f",
        "--folder-id",
        help="Google Drive folder ID (defaults to PUBLIC_FOLDER_ID from config)",
    )
    ap.add_argument(
        "-p",
        "--path",
        help="Local public folder path (defaults to PUBLIC_FOLDER_PATH from config)",
    )
    ap.add_argument(
        "-o",
        "--out",
        default="urls.json",
        help="Output JSON filename (default: urls.json, written to project root)",
    )
    ap.add_argument(
        "--csv",
        help="Optional CSV output filename (written to project root)",
    )
    ap.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Do not dedupe by filename (keep all matches)",
    )
    args = ap.parse_args()

    # Resolve inputs from CLI or config
    folder_id = args.folder_id or (cfg.public_folder_id() or "")
    if not folder_id:
        print(
            "No folder ID. Set PUBLIC_FOLDER_ID in .env or config/settings.json, or pass --folder-id.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Make pdf_root a definite Path (no unions)
    if args.path:
        pdf_root = Path(args.path)
    else:
        pf = cfg.public_folder_path()  # Optional[Path]
        if pf is None:
            print(
                "No public folder path. Set PUBLIC_FOLDER_PATH in .env or config/settings.json, or pass --path.",
                file=sys.stderr,
            )
            sys.exit(1)
        pdf_root = pf

    if not pdf_root.exists():
        print(f"Error: Folder not found: {pdf_root}", file=sys.stderr)
        sys.exit(1)

    all_pdfs = _find_pdfs(pdf_root)
    pdfs = all_pdfs if args.no_dedupe else _dedupe_keep_largest(all_pdfs)

    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    # Build mapping template
    mapping = {
        "_note": "Fill the 'id' with each file's Google Drive FILE ID (from the share link).",
        "folderId": folder_id,
        "count": len(pdfs),
        "files": [],
    }

    for p in pdfs:
        rel = p.relative_to(pdf_root)
        mapping["files"].append(
            {
                "filename": p.name,
                "path": str(rel),
                "id": "",  # <-- fill me with the Drive file ID
                "shareUrlExample": "https://drive.google.com/file/d/<ID>/view",
            }
        )

    out_json = ROOT / args.out
    out_json.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.csv:
        out_csv = ROOT / args.csv
        with out_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["filename", "path", "id"])
            writer.writeheader()
            for row in mapping["files"]:
                writer.writerow({"filename": row["filename"], "path": row["path"], "id": ""})

    # Friendly summary
    print(f"Folder ID: {folder_id}  (source: {'CLI' if args.folder_id else 'config'})")
    print(f"Public path: {pdf_root}  (source: {'CLI' if args.path else 'config'})")
    print(f"PDFs found: {len(pdfs)}  (scanned: {len(all_pdfs)} total)")
    print(f"JSON written: {out_json}")
    if args.csv:
        print(f"CSV written:  {ROOT / args.csv}")
    print("\nNext:")
    print("  1) Paste each file's Drive ID into the 'id' field")
    print("  2) Run your update script (e.g., update-site-data.py) to apply IDs to site data")


if __name__ == "__main__":
    main()
