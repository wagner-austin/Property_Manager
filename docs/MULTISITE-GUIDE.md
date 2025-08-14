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
├── css/main.css              # Main stylesheet (imports all modules)
├── css/base/                 # Base styles
├── css/components/           # Component styles  
├── css/layout/               # Layout styles
├── js/app-multisite.js       # Multi-site loader & renderer
├── sites/                    # Property-specific data
│   ├── lancaster-12/
│   │   └── data.json        # Lancaster configuration
│   ├── palmdale-8/
│   │   └── data.json        # Another property
│   └── ranchita-20/
│       └── data.json        # And another...
└── scripts/                  # Python automation tools
    ├── smart_site_mapper.py  # Intelligent file categorization
    ├── audit_drive_files.py  # Drive inventory generation
    ├── generate_url_template.py  # Create URL mapping template
    └── update_site_data.py   # Update site with Drive IDs
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

### Generate Site Data
```bash
# Run smart mapper to generate data.json
python scripts/smart_site_mapper.py

# Or generate URL template and update manually
python scripts/generate_url_template.py
python scripts/update_site_data.py
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

### Page Jumps
Currently uses Google Drive's built-in viewer. For advanced PDF features:
1. Consider integrating PDF.js (not currently implemented)
2. Google Drive viewer supports basic page navigation
3. Direct links work with `#page=N` parameter

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
- **Change styles**: Edit `css/main.css` or component-specific files in `css/components/`

## 🎉 Ready to Scale!

This architecture supports unlimited properties with minimal overhead. Just add a JSON file per property and you're done!