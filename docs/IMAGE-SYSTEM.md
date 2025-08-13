# Image Management System Documentation

## Overview

The Property Manager includes a comprehensive image management system that handles owner photos, company logos, and background images. The system supports both local files and Google Drive integration with automatic fallback support.

## Configuration

### Main Configuration File: `config/images.json`

The central configuration file that defines all image assets:

```json
{
  "owner": {
    "photo": {
      "src": "public/brand/owner/Rick-Reza-Profile-Picture.jpg",
      "alt": "Rick Reza",
      "caption": "Rick Reza — CEO",
      "loading": "eager",
      "display": true
    }
  },
  "logos": {
    "header": {
      "src": "public/brand/logos/Huntington-Beach-Capital-Partners-Logo.png",
      "alt": "Huntington Beach Capital Partners",
      "width": 280,
      "loading": "eager",
      "display": true
    },
    "footer": {
      "src": "public/brand/logos/Huntington-Beach-Capital-Partners-Logo.png",
      "alt": "Huntington Beach Capital Partners",
      "width": 180,
      "display": true
    }
  },
  "backgrounds": {
    "hero": {
      "image": "public/backgrounds/soft-black-creme--faint-marble-paper-professional-background.png",
      "overlay": "",
      "position": "center center",
      "size": "cover",
      "attachment": "fixed",
      "enabled": true
    }
  }
}
```

## Image System Features

### 1. Owner Profile Integration

The owner's profile photo is integrated directly into the hero section with responsive sizing:

- **Aspect Ratio**: Maintains 3:4 portrait ratio
- **Responsive Sizing**: `clamp(180px, 22vw, 260px)`
- **Styling**: White frame with opacity, square edges, professional shadow
- **Fallback**: SVG placeholder if image fails to load

### 2. Logo Management

#### Header Logo
- Automatically converted to white using CSS filters
- Responsive sizing: `clamp(240px, 28vw, 360px)`
- Left-aligned in the header
- Supports dark mode variants

#### Footer Logo
- Fixed size: 180px width
- Automatic white filter in dark footer
- Optional display control

### 3. Background Images

#### Hero Background
- Supports local files or Google Drive URLs
- Fixed attachment for parallax effect
- Custom overlay support with gradients
- Responsive positioning and sizing
- CSS custom properties for dynamic control

#### Section Backgrounds
- Individual backgrounds for plans and documents sections
- Optional overlay configuration
- Enable/disable per section

### 4. Lot Images

Dynamic image loading for property lots:

```javascript
// Lot image configuration in images.json
"lots": {
  "defaultImage": "public/lots/default-lot.jpg",
  "images": {
    "lot1": "public/lots/lot-1.jpg",
    "lot2": "public/lots/lot-2.jpg"
  }
}
```

## File Organization

### Directory Structure
```
public/
├── backgrounds/
│   └── soft-black-creme--faint-marble-paper-professional-background.png
├── brand/
│   ├── logos/
│   │   └── Huntington-Beach-Capital-Partners-Logo.png
│   └── owner/
│       └── Rick-Reza-Profile-Picture.jpg
└── lots/
    └── [lot images]
```

### Naming Conventions
- Use hyphens instead of spaces: `Rick-Reza-Profile-Picture.jpg`
- Descriptive names: `soft-black-creme--faint-marble-paper.png`
- Consistent format: lowercase with hyphens

## JavaScript Implementation

### Image Loading System (`js/images.js`)

The image loader provides:

1. **Automatic Configuration Loading**
   ```javascript
   const globalCfg = await loadJson('config/images.json');
   const siteCfg = siteSlug ? await loadJson(`sites/${siteSlug}/images.json`) : null;
   const cfg = deepMerge(globalCfg, siteCfg);
   ```

2. **Smart URL Resolution**
   - Detects Google Drive URLs and converts them
   - Handles local file paths
   - Provides fallback placeholders

3. **Dynamic Application**
   - Sets images via `src` attribute
   - Applies backgrounds via CSS custom properties
   - Handles loading and error states

4. **Debug Support**
   ```javascript
   window.ImagesDebug = {
     config: cfg,
     elements: { /* DOM elements */ },
     test: { /* utility functions */ }
   };
   ```

## CSS Integration

### CSS Custom Properties

The system uses CSS custom properties for dynamic styling:

```css
header[data-bg='hero'] {
  background-image:
    var(--hero-overlay, linear-gradient(...)),
    var(--hero-image, none);
  background-size: var(--hero-size, cover);
  background-position: var(--hero-position, center);
  background-attachment: var(--hero-attachment, scroll);
}
```

### Responsive Image Handling

```css
.owner-photo {
  width: clamp(180px, 22vw, 260px);
  aspect-ratio: 3 / 4;
  object-fit: contain;
}

.brand-logo {
  width: clamp(240px, 28vw, 360px);
  filter: brightness(0) invert(1);
}
```

## Usage Examples

### Adding a New Background

1. Add image to `public/backgrounds/`
2. Update `config/images.json`:
   ```json
   "backgrounds": {
     "hero": {
       "image": "public/backgrounds/new-background.jpg",
       "enabled": true
     }
   }
   ```
3. Image automatically loads on page refresh

### Updating Owner Photo

1. Add photo to `public/brand/owner/`
2. Update `config/images.json`:
   ```json
   "owner": {
     "photo": {
       "src": "public/brand/owner/new-photo.jpg",
       "caption": "New Caption",
       "display": true
     }
   }
   ```

### Site-Specific Images

Create `sites/[site-name]/images.json` to override global settings:

```json
{
  "backgrounds": {
    "hero": {
      "image": "public/backgrounds/site-specific-bg.jpg"
    }
  }
}
```

## Performance Optimization

### Loading Strategies

- **Eager Loading**: Owner photo and header logo (above the fold)
- **Lazy Loading**: Lot images and footer elements
- **Async Decoding**: Non-blocking image rendering

### Image Optimization

1. **Compress images** before adding to repository
2. **Use appropriate formats**:
   - JPEG for photos
   - PNG for logos with transparency
   - WebP for modern browser support

3. **Size guidelines**:
   - Backgrounds: Max 1920x1080, ~200-500KB
   - Owner photos: 600x800px, ~50-100KB
   - Logos: 2x display size, ~20-50KB

## Debugging

### Enable Debug Mode

Add `?debug=1` to URL or in console:
```javascript
window.Log.setEnabled(true);
window.Log.setLevel('debug');
```

### Check Image Status

```javascript
// View configuration
console.log(window.ImagesDebug.config);

// Check loaded elements
console.log(window.ImagesDebug.elements);

// Test URL conversion
window.ImagesDebug.test.pickUrl({src: 'test.jpg'});
```

### Common Issues

1. **Images not loading**:
   - Check file paths (use relative paths without leading slash)
   - Verify file exists in public folder
   - Check browser console for 404 errors

2. **Background not visible**:
   - Ensure `enabled: true` in config
   - Check overlay opacity (should be low or empty)
   - Verify CSS custom properties are applied

3. **Logo not white**:
   - CSS filter requires `brightness(0) invert(1)`
   - Check for conflicting styles
   - Ensure logo has transparent background

## Migration from Google Drive

To migrate from Drive-hosted images to local files:

1. Download images from Google Drive
2. Place in appropriate `public/` subdirectories
3. Update paths in `config/images.json`
4. Remove Drive IDs from configuration
5. Test locally with `make serve`

## Best Practices

1. **Always use relative paths** starting with `public/` (no leading slash)
2. **Maintain consistent naming** with hyphens
3. **Optimize images** before committing
4. **Test on multiple devices** for responsive behavior
5. **Use debug mode** to troubleshoot issues
6. **Keep backups** of original high-resolution images
7. **Document image sources** and licenses

## Future Enhancements

- [ ] WebP format support with fallbacks
- [ ] Automatic image optimization pipeline
- [ ] CDN integration for faster loading
- [ ] Dark mode image variants
- [ ] Image gallery component
- [ ] Lazy loading with intersection observer
- [ ] Progressive image loading