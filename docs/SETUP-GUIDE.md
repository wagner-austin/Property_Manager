# Lancaster 12 Lots - Setup & Deployment Guide

## 🏗️ Project Structure

```
LANCASTER 12 LOTS/
├── index.html              # Main entry point
├── sites/                  # Multi-site configurations
│   ├── lancaster-12/       # Lancaster property
│   │   └── data.json      # Site-specific data
│   └── _template/         # Template for new sites
│       └── data.json
├── js/                    # JavaScript files
│   └── app-multisite.js  # Main application logic
├── scripts/               # Python utilities
│   ├── get-drive-ids.py  # Auto-fetch Drive file IDs
│   └── audit-drive-files.py # Audit & organize files
└── Google Drive/
    └── Public/            # Public-facing documents
        └── lancaster-12/  # Property-specific PDFs
```

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Install dependencies
make deps

# Setup Google Drive API access
make drive-login
```

### 2. Organize Your Files

```bash
# Audit your Drive folder structure
make audit FOLDER_ID=<ROOT_FOLDER_ID> CHILD=Public

# Review the output and:
# 1. Create Public/lancaster-12 folder in Google Drive
# 2. Move PDFs to the Public/lancaster-12 folder
# 3. Remove duplicates
```

### 3. Configure the Site

Edit `sites/lancaster-12/data.json`:
```json
{
  "drive": {
    "publicFolderId": "<PUBLIC_LANCASTER_12_FOLDER_ID>"
  }
}
```

### 4. Sync Drive IDs

```bash
# Fetch and apply Drive file IDs
make drive-apply SITE=lancaster-12 FOLDER=<PUBLIC_FOLDER_ID>

# Or use the default (reads from data.json)
make drive-apply SITE=lancaster-12
```

### 5. Test Locally

```bash
# Start local server
make serve

# Opens: http://localhost:8000/?site=lancaster-12
```

## 📁 Google Drive Organization

### Recommended Structure
```
Your Drive/
├── Project Root/           # Code, scripts, private files
│   ├── credentials.json    # NEVER share publicly
│   ├── token.json         # NEVER share publicly
│   └── ... code files
└── Public/                # Share: "Anyone with link can view"
    ├── lancaster-12/      # Property-specific folder
    │   ├── PRESENTATION.pdf
    │   ├── PLAN 1.pdf
    │   └── ... other PDFs
    └── future-property/   # Easy to add more
```

### Security Best Practices
- ✅ Only share the `Public` folder
- ✅ Keep credentials in project root
- ✅ Use `publicFolderId` in data.json
- ❌ Never share the project root folder

## 🔧 Common Commands

### File Management
```bash
# Audit files (compare root vs Public)
make audit FOLDER_ID=<ROOT_ID> CHILD=Public

# Update Drive IDs after moving files
make drive-apply SITE=lancaster-12

# Verbose mode for debugging
python scripts/get-drive-ids.py --site lancaster-12 --verbose --dry-run
```

### Development
```bash
# Start local server
make serve

# Create deployment package
make pack

# Run tests
make test
```

### Adding New Properties
```bash
# Create new site from template
make new SITE=palmdale-8

# Edit sites/palmdale-8/data.json with:
# - Property details
# - publicFolderId for the new Public/palmdale-8 folder

# Sync Drive IDs
make drive-apply SITE=palmdale-8
```

## 🔍 How File Matching Works

The `get-drive-ids.py` script intelligently matches your configuration to Drive files:

### Matching Algorithm
1. **Normalizes** both config titles and file names (lowercase, remove punctuation)
2. **Scores** matches based on:
   - Token matching (words in common)
   - Special patterns (Plan 1, Lot 5, etc.)
   - Document types (presentation, entitlements, LLC info)
3. **Selects** the highest scoring match

### Examples
- Config: `"Plan 1"` → Matches: `"LANCASTER PLAN 1 PLANS.pdf"`
- Config: `"Tentative Map"` → Matches: `"LANCASTER 12 LOT PLATMAP.pdf"`
- Config: `"LLC Information"` → Matches: `"LANCASTER 43741 LLC INFO.pdf"`

### Debugging Matches
```bash
# See detailed matching scores
python scripts/get-drive-ids.py --site lancaster-12 --verbose --dry-run
```

## 🚢 Deployment to GitHub Pages

### 1. Prepare Repository
```bash
# Initialize git (if not already)
git init

# Add files (.gitignore already configured)
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/lancaster-properties.git
git push -u origin main
```

### 2. Enable GitHub Pages
1. Go to Settings → Pages in your GitHub repo
2. Source: Deploy from branch
3. Branch: main, folder: / (root)
4. Save

### 3. Access Your Site
```
https://YOUR_USERNAME.github.io/lancaster-properties/?site=lancaster-12
```

## 🔐 Security Checklist

### Before Deploying
- [ ] All PDFs in Public folder only
- [ ] No credentials in repository
- [ ] `.gitignore` includes sensitive files
- [ ] `publicFolderId` points to Public subfolder
- [ ] Public folder shared as "View only"

### Files That Should NEVER Be Committed
```
credentials.json    # Google API credentials
token.json         # OAuth token
*.bak.*.json      # Backup files
file-mapping.json  # Audit outputs
```

## 🐛 Troubleshooting

### Files Not Matching
```bash
# Check with verbose mode
python scripts/get-drive-ids.py --site lancaster-12 --verbose

# Common issues:
# - File renamed in Drive but not in config
# - Scores too low (adjust matching algorithm)
# - Wrong folder ID
```

### Unicode/Emoji Errors on Windows
The scripts include UTF-8 encoding fixes. If you still see errors:
```bash
# Set environment variable
set PYTHONIOENCODING=utf-8

# Or use Windows Terminal (recommended)
```

### Drive API Issues
```bash
# Re-authenticate
rm token.json
make drive-login

# Check credentials
ls credentials.json  # Should exist
```

## 📝 Configuration Reference

### sites/SITE_NAME/data.json
```json
{
  "slug": "lancaster-12",
  "drive": {
    "publicFolderId": "ID_OF_PUBLIC_SUBFOLDER",  // Preferred
    "folderId": "FALLBACK_FOLDER_ID"            // Fallback
  },
  "presentation": {
    "title": "Complete Presentation",  // Used for matching
    "file": "DRIVE_FILE_ID"           // Auto-populated
  },
  "plans": [...],
  "lots": [...],
  "projectDocs": [...]
}
```

### Folder ID Priority
The system looks for folder IDs in this order:
1. `drive.publicFolderId`
2. `contact.publicFolderId`
3. `publicFolderId` (top-level)
4. `drive.folderId`
5. `contact.folderId`
6. `folderId` (top-level)

## 🔄 Workflow Summary

### For Each New Property
1. **Create** `Public/property-name` folder in Drive
2. **Upload** PDFs to that folder
3. **Run** `make new SITE=property-name`
4. **Edit** `sites/property-name/data.json`
5. **Set** `publicFolderId` to the new folder
6. **Run** `make drive-apply SITE=property-name`
7. **Test** with `make serve`
8. **Deploy** to GitHub Pages

## 📞 Support

For issues or questions:
- Check this guide first
- Review verbose output: `--verbose` flag
- Check file permissions in Google Drive
- Ensure Public folder is shared correctly