#!/usr/bin/env python3
"""
One-time setup for Google Drive API access
This will help you get credentials to automate Drive operations
"""

import sys
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import config_loader as cfg
else:
    try:
        from . import config_loader as cfg  # python -m scripts.setup_drive_api
    except ImportError:
        import config_loader as cfg  # python scripts/setup_drive_api.py


def main():
    print("=" * 60)
    print("GOOGLE DRIVE API SETUP")
    print("=" * 60)
    print("\nThis will help you set up automated Drive access.\n")

    print("STEP 1: Enable Google Drive API")
    print("-" * 40)
    print("1. I'll open the Google Cloud Console")
    print("2. Create a new project (or select existing)")
    print("3. Enable the Google Drive API")
    print("4. Create credentials (OAuth 2.0 Client ID)")
    print("5. Download the credentials.json file")
    print()

    input("Press Enter to open Google Cloud Console...")

    # Open the quickstart page which has the Enable API button
    webbrowser.open("https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com")

    print("\nIn the browser:")
    print("1. Click 'SELECT PROJECT' or create new")
    print("2. Name it something like 'Lancaster Properties'")
    print("3. Click 'ENABLE' for Google Drive API")
    print()

    input("Press Enter after enabling the API...")

    print("\nSTEP 2: Create OAuth Credentials")
    print("-" * 40)
    print("Now we need to create credentials:")
    print()

    webbrowser.open("https://console.cloud.google.com/apis/credentials")

    print("In the browser:")
    print("1. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
    print("2. If prompted, configure consent screen:")
    print("   - User Type: External")
    print("   - App name: Lancaster Properties")
    print("   - Your email for support")
    print("   - Add your email to test users")
    print("3. For Application type: Choose 'Desktop app'")
    print("4. Name: 'Lancaster Drive Access'")
    print("5. Click 'CREATE'")
    print("6. Click 'DOWNLOAD JSON' on the popup")
    print()

    cred_path, _ = cfg.credentials_paths()
    print(f"7. Save the downloaded file as:\n   {cred_path}")
    print()

    input("Press Enter after saving credentials.json...")

    if not cred_path.exists():
        print("\nERROR: credentials.json not found!")
        print(f"Please save it to: {cred_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNow you can run:")
    print("  python -m scripts.get_drive_ids")
    print("\nThis will:")
    print("- Authenticate once (browser popup)")
    print("- Automatically get all PDF file IDs")
    print("- Update urls.json with real IDs")
    print("- No more manual copying!")

    # Create .gitignore to not commit credentials
    gitignore = Path(__file__).parent.parent / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if "credentials.json" not in content:
            gitignore.write_text(content + "\ncredentials.json\ntoken.json\n")
    else:
        gitignore.write_text("credentials.json\ntoken.json\n*.bak.*\n.server.pid\n")

    print("\nNote: credentials.json and token.json added to .gitignore")


if __name__ == "__main__":
    main()
