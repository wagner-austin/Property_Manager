# Quick Reference Guide

## Common Tasks

### Start Development Server
```bash
make serve
# Visit: http://localhost:8000/?site=lancaster-12
```

### Enable Debug Mode
```
http://localhost:8000/?site=lancaster-12&debug=1
```

### Update Site Data
```bash
python scripts/smart_site_mapper.py
```

### Deploy to Production
```bash
make pack
# Upload deployment.zip to hosting
```

## File Locations

| Content | Location |
|---------|----------|
| Main HTML | `index.html` |
| Site Data | `sites/[site-name]/data.json` |
| Images Config | `config/images.json` |
| Site Config | `sites.config.json` |
| Owner Photo | `public/brand/owner/` |
| Logos | `public/brand/logos/` |
| Backgrounds | `public/backgrounds/` |
| JavaScript | `js/` |
| Styles | `css/styles.css` |

## Configuration Quick Reference

### Change Owner Photo
Edit `config/images.json`:
```json
{
  "owner": {
    "photo": {
      "src": "public/brand/owner/new-photo.jpg"
    }
  }
}
```

### Change Logo
Edit `config/images.json`:
```json
{
  "logos": {
    "header": {
      "src": "public/brand/logos/new-logo.png"
    }
  }
}
```

### Change Background
Edit `config/images.json`:
```json
{
  "backgrounds": {
    "hero": {
      "image": "public/backgrounds/new-bg.jpg"
    }
  }
}
```

### Add New Lot Details
Edit `sites.config.json`:
```json
{
  "lot_details": {
    "1": {
      "apn": "1234-567-890",
      "address": "123 Main St",
      "status": "Available"
    }
  }
}
```

## Console Commands

### Debug Images
```javascript
// View image configuration
window.ImagesDebug.config

// Check loaded elements
window.ImagesDebug.elements

// Test URL conversion
window.ImagesDebug.test.pickUrl({src: 'test.jpg'})
```

### Debug Logging
```javascript
// Enable all logging
window.Log.setEnabled(true);
window.Log.setLevel('debug');

// Check current site
window.currentSite
```

## Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all commands |
| `make deps` | Install dependencies |
| `make serve` | Start local server |
| `make debug` | Start with debug logging |
| `make lint` | Run code linters |
| `make lint` | Auto-fix and format all code |
| `make drive-audit` | Audit Drive files |
| `python scripts/smart_site_mapper.py` | Run smart mapper |
| `make pack` | Create deployment package |
| `make clean` | Remove generated files |

## Python Scripts

| Script | Purpose |
|--------|---------|
| `smart_site_mapper.py` | Generate site data from Drive inventory |
| `audit_drive_files.py` | Create Drive file inventory |
| `setup_drive_api.py` | Configure Google Drive API |

## URL Parameters

| Parameter | Example | Purpose |
|-----------|---------|---------|
| `site` | `?site=lancaster-12` | Load specific site |
| `debug` | `?debug=1` | Enable debug logging |
| `debugImages` | `?debugImages=1` | Debug image loading |

## CSS Classes

### Key Layout Classes
- `.container` - Content wrapper
- `.hero-with-owner` - Hero section with profile
- `.lots-grid` - Lot cards grid
- `.plans-grid` - Plan cards grid
- `.documents-grid` - Document cards grid

### Component Classes
- `.owner-photo` - Owner profile image
- `.brand-logo` - Company logo
- `.primary-cta` - Main call-to-action button
- `.btn-small` - Secondary buttons
- `.pdf-modal` - PDF viewer modal

## Image Requirements

| Image Type | Recommended Size | Format |
|------------|-----------------|--------|
| Owner Photo | 600x800px | JPEG |
| Logo | 500x150px | PNG |
| Background | 1920x1080px | JPEG |
| Lot Images | 800x500px | JPEG |

## Git Workflow

### Make Changes
```bash
git add .
git commit -m "Update: description"
git push origin main
```

### Deploy to GitHub Pages
```bash
git push origin main
# Automatically deploys if Pages is enabled
```

## Troubleshooting Checklist

### Images Not Loading
- [ ] File path starts with `public/` (no leading slash)
- [ ] File exists in correct directory
- [ ] File name matches exactly (case-sensitive)
- [ ] Check browser console for 404 errors

### Site Not Loading
- [ ] Site exists in `sites.config.json`
- [ ] `sites/[name]/data.json` exists
- [ ] URL parameter is correct: `?site=name`
- [ ] Check browser console for errors

### PDFs Not Opening
- [ ] Drive file has "Anyone with link" permission
- [ ] File ID is correct in data.json
- [ ] Not blocked by browser/network
- [ ] Try "Open in Drive" link

### Changes Not Showing
- [ ] Clear browser cache (Ctrl+Shift+R)
- [ ] Check you're editing correct file
- [ ] Restart local server
- [ ] Check for JavaScript errors

## Contact Information

**Property Manager Support**
- Documentation: This folder (`docs/`)
- Issues: Check browser console first

**Huntington Beach Capital Partners**
- Phone: 714-713-8618
- Email: rickreza@yahoo.com

## Quick Links

- [Full Documentation](README.md)
- [Configuration Guide](CONFIGURATION.md)
- [Image System](IMAGE-SYSTEM.md)
- [API Reference](API-REFERENCE.md)
- [Deployment Guide](DEPLOY.md)