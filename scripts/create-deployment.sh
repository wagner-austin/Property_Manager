#!/usr/bin/env bash
set -euo pipefail

# Go to project root (this script lives in scripts/)
cd "$(dirname "$0")/.."

# Require 'zip'
if ! command -v zip >/dev/null 2>&1; then
  echo "Error: 'zip' not found. Install it:"
  echo "  macOS:  brew install zip"
  echo "  Ubuntu: sudo apt-get install zip"
  echo "  RHEL:   sudo yum install zip"
  exit 1
fi

# Allow custom output name via argument, default to deployment.zip
OUT="${1:-deployment.zip}"

# Build include list only from things that exist
INCLUDE=()
[[ -f index.html ]]  && INCLUDE+=( "index.html" )
[[ -f styles.css ]]  && INCLUDE+=( "styles.css" )
[[ -f app.js ]]      && INCLUDE+=( "app.js" )
[[ -f data.js ]]     && INCLUDE+=( "data.js" )
[[ -d css ]]         && INCLUDE+=( "css" )
[[ -d js ]]          && INCLUDE+=( "js" )
[[ -d images ]]      && INCLUDE+=( "images" )
[[ -d assets ]]      && INCLUDE+=( "assets" )
[[ -f favicon.ico ]] && INCLUDE+=( "favicon.ico" )

# Check we have minimum required files
if [[ ! -f index.html ]]; then
  echo "Error: index.html not found in project root"
  exit 1
fi

if [[ ${#INCLUDE[@]} -eq 0 ]]; then
  echo "Error: No files found to package"
  exit 1
fi

# Start fresh
rm -f "$OUT"

# Zip it up, excluding OS/editor/git files
# Note: Using */ for recursive patterns that work across all zip versions
zip -r "$OUT" "${INCLUDE[@]}" \
  -x "*/.DS_Store" \
     "*/Thumbs.db" \
     "*/desktop.ini" \
     ".git/*" \
     ".gitignore" \
     "*.swp" \
     "*~" \
     "$OUT" > /dev/null

# Success message
echo
echo "✅ Created $OUT ($(du -h "$OUT" | cut -f1))"
echo "📦 Contains: ${INCLUDE[*]}"
echo
echo "Next steps:"
echo "  1. Test locally: unzip -l $OUT"
echo "  2. Deploy: drag $OUT to app.netlify.com/drop (or any static host)"
echo "  3. Or extract and upload"