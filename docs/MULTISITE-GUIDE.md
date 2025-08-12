# 🏗️ Multi-Site Property Marketing Platform

## ✅ What We Built

A **reusable, multi-property marketing website** that can showcase unlimited development properties from a single codebase. Each property gets its own configuration file but shares the same HTML/CSS/JS.

## 🚀 Key Features

- **Multi-site support**: `?site=lancaster-12`, `?site=palmdale-8`, etc.
- **Drive & external PDFs**: Works with Google Drive IDs or any PDF URL
- **Theme per property**: Each site can have custom colors
- **Page jumps**: PDF.js support for deep-linking to specific pages
- **Mobile responsive**: Sticky contact bar on phones
- **Zero backend**: Pure static files, hosts anywhere
- **Build tools**: Scripts to auto-generate Drive URLs

## 📁 Architecture

```
/
├── index.html                 # Main app (reads ?site= parameter)
├── css/styles.css            # Shared styles
├── js/app-multisite.js       # Multi-site loader & renderer
├── sites/                    # Property-specific data
│   ├── lancaster-12/
│   │   └── data.json        # Lancaster configuration
│   ├── palmdale-8/
│   │   └── data.json        # Another property
│   └── ranchita-20/
│       └── data.json        # And another...
└── scripts/                  # Build & test tools
    ├── get-drive-urls.py    # Generate Drive URL template
    ├── update-data-js.py    # Auto-fill data.json
    └── test-multisite.html  # Test page for all sites
```

## 🎯 Quick Start

### Test Current Site
```bash
make serve
# Open: http://localhost:8000/?site=lancaster-12
```

### Add New Property
```bash
make new SITE=palmdale-8
# Creates: sites/palmdale-8/data.json
# Edit the JSON, then access via: ?site=palmdale-8
```

### Get Drive URLs
```bash
python scripts/get-drive-urls.py
# Creates urls.json template
# Fill in Drive IDs, then:
python scripts/update-data-js.py
```

### Deploy
```bash
make pack
# Creates deployment.zip
# Upload to Netlify/Vercel/GitHub Pages
```

## 📝 Data Structure

Each site's `data.json` contains:

```json
{
  "slug": "lancaster-12",
  "brand": {
    "title": "Lancaster 12 Lots",
    "tagline": "Premium Development Properties",
    "theme": {
      "primary": "#1a365d",
      "accent": "#2563eb"
    }
  },
  "contact": {
    "companyName": "Huntington Beach Capital Partners, Inc.",
    "phoneDisplay": "714-713-8618",
    "phoneE164": "+17147138618",
    "email": "rickreza@yahoo.com",
    "folderId": "DRIVE_FOLDER_ID"
  },
  "location": {
    "city": "Lancaster",
    "state": "CA"
  },
  "viewer": "drive",  // or "pdfjs" for page jumps
  "presentation": {...},
  "lots": [...],
  "plans": [...],
  "projectDocs": [...]
}
```

## 🔗 URL Examples

- **Default**: `https://yoursite.com/` → lancaster-12
- **Specific**: `https://yoursite.com/?site=palmdale-8`
- **Share link**: `https://yoursite.com/?site=ranchita-20`

## 🎨 Customization

### Per-Property Themes
Each property can set custom colors in `data.json`:
```json
"theme": {
  "primary": "#1a365d",
  "accent": "#2563eb",
  "success": "#10b981"
}
```

### External PDFs
Works with any PDF URL, not just Drive:
```json
"file": "https://example.com/docs/plan.pdf"
```

### Page Jumps (PDF.js)
1. Install PDF.js to `vendor/pdfjs/`
2. Set `"viewer": "pdfjs"` in data.json
3. Use `"page": 5` to jump to page 5

## ✨ Benefits

1. **One codebase**: Maintain one site, deploy many properties
2. **No OAuth**: Build-time scripts, no runtime auth needed
3. **SEO friendly**: Each property gets unique URL
4. **Fast**: Static files, CDN-ready
5. **Flexible**: Drive, external URLs, or local PDFs

## 🚧 Adding Properties

1. **Create site folder**:
   ```bash
   make new SITE=my-property
   ```

2. **Edit data**:
   ```bash
   vim sites/my-property/data.json
   ```

3. **Add Drive IDs**:
   - Upload PDFs to Drive
   - Get share links
   - Paste IDs into data.json

4. **Test**:
   ```bash
   make serve
   # Open: http://localhost:8000/?site=my-property
   ```

5. **Deploy**:
   ```bash
   make pack
   # Upload deployment.zip
   ```

## 📊 Portfolio Page (Optional)

Create `portfolio.html` listing all properties:

```html
<div class="properties">
  <a href="/?site=lancaster-12">Lancaster 12 Lots</a>
  <a href="/?site=palmdale-8">Palmdale 8 Units</a>
  <a href="/?site=ranchita-20">Ranchita 20 Acres</a>
</div>
```

## 🛠️ Maintenance

- **Update all sites**: Edit `js/app-multisite.js`
- **Update one site**: Edit `sites/[slug]/data.json`
- **Add features**: Extend renderer functions in app-multisite.js
- **Change styles**: Edit `css/styles.css` (affects all sites)

## 🎉 Ready to Scale!

This architecture supports unlimited properties with minimal overhead. Just add a JSON file per property and you're done!