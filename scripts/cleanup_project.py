#!/usr/bin/env python3
"""
Project cleanup script to remove deprecated files and organize the structure.
Run with --dry-run first to see what would be done.
"""

import argparse
import io
import sys

# Fix Windows encoding for emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

# Files to remove (deprecated/obsolete)
DEPRECATED_FILES = [
    "js/app.js",
    "js/data.js",
    "data-js-snippets.txt",
    "urls-instructions.txt",
    "urls.csv",
]

# Patterns for backup files to remove
BACKUP_PATTERNS = [
    "*.bak.*.json",
    "*.bak",
    "*~",
    "*.tmp",
]

# Windows system files to remove
SYSTEM_FILES = [
    "desktop.ini",
    "Thumbs.db",
    ".DS_Store",
]

# Files to rename for clarity
RENAME_MAP = {
    "scripts/update-data-js.py": "scripts/update-site-data.py",
    "scripts/get-drive-urls.py": "scripts/generate-url-template.py",
}

# Directories to never touch
IGNORE_DIRS = {".git", "node_modules", "logs", ".trash"}

# Case-insensitive ignore set for Windows compatibility
IGNORE_DIRS_LOWER = {d.lower() for d in IGNORE_DIRS}

# Pattern for problematic filenames
BAD_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._\- ()]")

# Global project root (set in cleanup_project)
project_root = None


def relpath(p: Path) -> str:
    """Get relative path safely, with fallback."""
    p = Path(p).resolve()
    if project_root is None:
        # Best-effort until project_root is initialized
        return str(p)
    try:
        return str(p.relative_to(project_root))
    except Exception:
        # Fallback: robust relative computation across OS
        import os as _os

        return _os.path.relpath(str(p), str(project_root))


def list_files(root, ignore_dirs=IGNORE_DIRS_LOWER):
    """List all files, skipping dangerous directories."""
    for p in Path(root).rglob("*"):
        if p.is_file() and not any(part.lower() in ignore_dirs for part in p.parts):
            yield p


def find_duplicates(project_root):
    """Find duplicate files by content hash and size."""
    by_sig = {}
    for p in list_files(project_root):
        try:
            bs = p.read_bytes()
        except Exception:
            continue
        sig = (hashlib.md5(bs).hexdigest(), len(bs))
        by_sig.setdefault(sig, []).append(p)

    dups = [v for v in by_sig.values() if len(v) > 1]
    if dups:
        print("\n🔁 Duplicate files (content-identical):")
        for group in dups:
            print("  ---")
            for f in group:
                print(f"    {relpath(f)}")
    else:
        print("\n✅ No content-identical duplicates found.")

    return len(dups)


def audit_names(project_root):
    """Audit filenames for potential issues."""
    issues = []
    for p in list_files(project_root):
        name = p.name
        rel_path = relpath(p)

        problems = []
        if len(name) > 90:
            problems.append("name too long")
        if "copy" in name.lower() or " copy" in name.lower():
            problems.append("contains 'copy'")
        if "(1)" in name or "(2)" in name:
            problems.append("numbered duplicate pattern")
        if BAD_NAME_PATTERN.search(name):
            problems.append("special characters")

        if problems:
            issues.append((rel_path, problems))

    print("\n📝 Naming audit:")
    if issues:
        print("  ⚠️  Files with naming issues (review/rename manually):")
        for path, problems in issues:
            print(f"    {path}: {', '.join(problems)}")
    else:
        print("  ✅ No naming issues detected.")

    return len(issues)


def move_to_trash(path: Path, trash_dir: Path) -> None:
    """Move file to trash directory instead of deleting."""
    trash_dir.mkdir(exist_ok=True)
    # Create a safe filename preserving directory structure
    target = trash_dir / relpath(path).replace("\\", "__").replace("/", "__")
    target.parent.mkdir(parents=True, exist_ok=True)

    # Handle existing files in trash
    counter = 1
    original_target = target
    while target.exists():
        stem = original_target.stem
        suffix = original_target.suffix
        target = original_target.parent / f"{stem}_{counter}{suffix}"
        counter += 1

    shutil.move(str(path), str(target))


def cleanup_project(dry_run=True, verbose=False, use_trash=False):
    """Clean up deprecated and unnecessary files."""

    global project_root
    project_root = Path(__file__).resolve().parent.parent

    trash_dir = project_root / ".trash"
    removed_count = 0
    renamed_count = 0

    print(f"{'DRY RUN - ' if dry_run else ''}Project Cleanup")
    print("=" * 50)

    # Remove deprecated files
    print("\n📁 Removing deprecated files...")
    for file_path in DEPRECATED_FILES:
        path = project_root / file_path
        if path.exists():
            print(f"  ❌ {relpath(path)}")
            if not dry_run:
                if use_trash:
                    move_to_trash(path, trash_dir)
                else:
                    path.unlink()
            removed_count += 1
        elif verbose:
            print(f"  ⏭️  {file_path} (already removed)")

    # Remove backup files
    print("\n🗑️  Removing backup files...")
    for pattern in BACKUP_PATTERNS:
        for path in project_root.rglob(pattern):
            if not path.is_dir() and not any(part.lower() in IGNORE_DIRS_LOWER for part in path.parts):
                print(f"  ❌ {relpath(path)}")
                if not dry_run:
                    if use_trash:
                        move_to_trash(path, trash_dir)
                    else:
                        path.unlink()
                removed_count += 1

    # Remove system files
    print("\n🖥️  Removing system files...")
    for sys_file in SYSTEM_FILES:
        for path in project_root.rglob(sys_file):
            if not path.is_dir() and not any(part.lower() in IGNORE_DIRS_LOWER for part in path.parts):
                print(f"  ❌ {relpath(path)}")
                if not dry_run:
                    if use_trash:
                        move_to_trash(path, trash_dir)
                    else:
                        path.unlink()
                removed_count += 1

    # Rename files for clarity
    print("\n✏️  Renaming files for clarity...")
    for old_name, new_name in RENAME_MAP.items():
        old_path = project_root / old_name
        new_path = project_root / new_name

        if old_path.exists():
            print(f"  📝 {relpath(old_path)} → {relpath(new_path)}")
            if not dry_run:
                old_path.rename(new_path)
            renamed_count += 1
        elif new_path.exists() and verbose:
            print(f"  ✅ {relpath(new_path)} (already renamed)")

    # Find duplicates if verbose
    if verbose:
        find_duplicates(project_root)

    # Audit naming
    name_issues = audit_names(project_root)

    # Check for problematic files in Public/
    print("\n📂 Public folder audit:")
    public_dir = project_root / "Public"
    if public_dir.exists():
        docx_files = list(public_dir.rglob("*.docx"))
        html_files = list(public_dir.rglob("*.html"))

        if docx_files:
            print("  ⚠️  Word documents in Public/ (consider converting to PDF):")
            for f in docx_files:
                print(f"    {relpath(f)}")

        if html_files:
            print("  ⚠️  HTML files in Public/ (verify if intentional):")
            for f in html_files:
                print(f"    {relpath(f)}")

        if not docx_files and not html_files:
            print("  ✅ No problematic file types detected")

    # Create .gitignore if it doesn't exist
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("\n📝 Creating .gitignore...")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project specific
token.json
credentials.json
*.bak
*.bak.*
*.tmp
deployment.zip
.trash/

# Test outputs
test-results/
coverage/
"""
        if not dry_run:
            gitignore_path.write_text(gitignore_content)
        print("  ✅ Created .gitignore")

    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Files to remove: {removed_count}")
    print(f"  Files to rename: {renamed_count}")
    print(f"  Naming issues: {name_issues}")

    if dry_run:
        print("\n⚠️  This was a DRY RUN. No files were actually modified.")
        print("Run with 'python scripts/cleanup-project.py --execute' to apply changes.")
        if not use_trash:
            print("Add --trash flag to move files to .trash/ instead of deleting.")
    else:
        print("\n✅ Cleanup complete!")
        if use_trash:
            print(f"📦 Removed files moved to {trash_dir}/")

        # Create a cleanup log
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, "w") as f:
            f.write(f"Cleanup performed at {datetime.now()}\n")
            f.write(f"Files removed: {removed_count}\n")
            f.write(f"Files renamed: {renamed_count}\n")
            f.write(f"Trash mode: {use_trash}\n")
        print(f"📋 Log saved to {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Clean up project files")
    parser.add_argument("--execute", action="store_true", help="Actually perform the cleanup (default is dry-run)")
    parser.add_argument("--trash", action="store_true", help="Move files to .trash/ instead of deleting")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show more detailed output (includes duplicate detection)"
    )

    args = parser.parse_args()

    # If --execute is specified, it's not a dry run
    dry_run = not args.execute

    cleanup_project(dry_run=dry_run, verbose=args.verbose, use_trash=args.trash)


if __name__ == "__main__":
    main()
