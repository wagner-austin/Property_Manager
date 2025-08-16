# Architecture Overview

## System Architecture

The Property Manager is a static web application with a modular architecture designed for scalability and maintainability.

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   HTML/CSS   │  │  JavaScript  │  │    Images    │ │
│  │   (Static)   │  │   (Dynamic)  │  │   (Local)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│          │                 │                 │          │
│          └─────────────────┼─────────────────┘          │
│                           │                             │
│                    ┌──────────────┐                     │
│                    │  Site Data   │                     │
│                    │    (JSON)    │                     │
│                    └──────────────┘                     │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
                 ┌──────────────────┐
                 │  Google Drive API │
                 │   (Documents)     │
                 └──────────────────┘
```

## Component Architecture

### Frontend Components

```
index.html
    ├── Header
    │   ├── Logo
    │   └── Hero Section
    │       ├── Owner Profile
    │       ├── Title/Tagline
    │       └── CTA Buttons
    ├── Main Content
    │   ├── Lots Grid
    │   ├── Plans Section
    │   └── Documents Grid
    ├── Footer
    └── PDF Modal
```

### JavaScript Modules

```
js/
├── app-multisite.js    # Core application logic
│   ├── Site Loader
│   ├── Data Renderer
│   └── Event Handlers
├── images.js           # Image management
│   ├── Config Loader
│   ├── URL Resolver
│   └── DOM Updater
└── logger.js           # Logging system
    ├── Log Levels
    └── Debug Interface
```

### Data Flow

```
1. Page Load
   ↓
2. Parse URL Parameters (?site=xxx)
   ↓
3. Load Site Configuration
   ├── sites/[site]/data.json
   └── config/images.json
   ↓
4. Render Components
   ├── Apply Images
   ├── Render Lots
   ├── Render Plans
   └── Render Documents
   ↓
5. Attach Event Handlers
   ├── PDF Viewer
   └── Contact Actions
```

## File Structure

### Static Assets

```
public/
├── backgrounds/        # Background images
│   └── *.jpg/png
├── brand/             # Brand assets
│   ├── logos/         # Company logos
│   └── owner/         # Owner photos
└── lots/              # Lot images
    └── *.jpg
```

### Configuration

```
config/
├── images.json        # Image configuration
├── credentials.json   # Google API (git-ignored)
└── settings.json      # Global settings
```

### Site Data

```
sites/
└── [site-name]/
    ├── data.json      # Site configuration
    └── images.json    # Site-specific images (optional)
```

## Module Details

### 1. Multi-Site Application (`app-multisite.js`)

**Purpose**: Core application logic for loading and rendering sites.

**Key Functions**:
- `loadSiteData()` - Fetches site configuration
- `renderSite()` - Orchestrates rendering
- `renderLots()` - Creates lot cards
- `renderPlans()` - Creates plan cards
- `renderDocuments()` - Creates document cards
- `openPDF()` - Handles PDF viewing

**Dependencies**:
- Site data JSON files
- Google Drive API for documents

### 2. Image Management System (`images.js`)

**Purpose**: Dynamic image loading with fallback support.

**Key Features**:
- Configuration-driven
- Google Drive support
- Local file support
- Placeholder fallbacks
- Debug interface

**Process**:
```javascript
Config Load → URL Resolution → DOM Update → Error Handling
```

### 3. Logging System (`logger.js`)

**Purpose**: Debugging and monitoring.

**Features**:
- Multiple log levels
- Prefixed loggers
- Enable/disable control
- URL parameter activation

### 4. Modal System

**Purpose**: Display PDF documents in an overlay modal.

**Key Features**:
- Google Drive document preview
- Local PDF file support
- Mobile-friendly navigation
- Keyboard and touch controls

**Closing Methods**:
- ESC key press
- Back button (mobile devices via hash navigation)
- Click outside modal
- X button in header

**Technical Implementation**:
- Uses URL hash (`#pdf-modal`) for back button support
- Tracks modal state with `pdfModalOpen` flag
- Listens to `hashchange` event for mobile back button
- Cleans up hash on modal close

## Design Patterns

### 1. Module Pattern

Each JavaScript file is an IIFE (Immediately Invoked Function Expression):

```javascript
(async function() {
  // Private scope
  const privateVar = 'hidden';
  
  // Public interface
  window.PublicAPI = {
    method: () => {}
  };
})();
```

### 2. Configuration-Driven

All customization through JSON configuration:

```javascript
const config = await loadJson('config/file.json');
applyConfig(config);
```

### 3. Progressive Enhancement

Base functionality works without JavaScript:

```html
<!-- Works without JS -->
<a href="tel:+17147138618">Call</a>

<!-- Enhanced with JS -->
<button onclick="openPDF(...)">View PDF</button>
```

### 4. Responsive Design

Mobile-first with progressive breakpoints:

```css
/* Mobile */
.container { padding: 20px; }

/* Tablet */
@media (min-width: 768px) {
  .container { padding: 40px; }
}

/* Desktop */
@media (min-width: 1024px) {
  .container { padding: 60px; }
}
```

## State Management

### Application State

```javascript
// Global state objects
window.currentSite = {
  slug: 'lancaster-12',
  data: {...}
};

window.ImagesDebug = {
  config: {...},
  elements: {...}
};
```

### URL State

Site selection via URL parameters:

```
https://site.com/?site=lancaster-12
```

### Local Storage

Persistent user preferences:

```javascript
localStorage.setItem('lastSite', 'lancaster-12');
localStorage.setItem('debugEnabled', 'true');
```

## Performance Optimization

### 1. Asset Loading

```javascript
// Eager load critical assets
loading="eager"  // Owner photo, header logo

// Lazy load below-fold content
loading="lazy"   // Lot images, footer
```

### 2. Image Optimization

- Compressed images (~70% quality)
- Appropriate formats (JPEG for photos, PNG for logos)
- Responsive sizing with `clamp()`

### 3. CSS Optimization

- CSS custom properties for theming
- Minimal specificity
- Hardware acceleration for animations

### 4. JavaScript Optimization

- Async/await for non-blocking operations
- Event delegation for dynamic content
- Debouncing for resize handlers

## Security Considerations

### 1. No Sensitive Data in Frontend

```javascript
// Never include in frontend code:
// - API keys
// - Credentials
// - Private URLs
```

### 2. Content Security Policy

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               img-src 'self' https://drive.google.com;
               frame-src https://drive.google.com;">
```

### 3. Input Validation

```javascript
// Sanitize user input
const siteSlug = params.get('site').replace(/[^a-z0-9-]/g, '');
```

## Browser Compatibility

### Target Browsers

- Chrome 90+ (2021)
- Firefox 88+ (2021)
- Safari 14+ (2020)
- Edge 90+ (2021)

### Polyfills & Fallbacks

```javascript
// Aspect ratio fallback
@supports not (aspect-ratio: 1) {
  .image-container {
    padding-top: 62.5%; /* 16:10 */
  }
}
```

## Development Workflow

### 1. Local Development

```bash
make serve  # Start local server
# Edit files
# Browser auto-refresh
```

### 2. Testing

```bash
make lint    # Check code quality
make test    # Run tests
?debug=1     # Enable debug mode
```

### 3. Build & Deploy

```bash
make pack    # Create deployment package
# Upload to hosting
```

## Extension Points

### Adding New Sites

1. Create configuration in `sites.config.json`
2. Run smart mapper
3. Site automatically available

### Adding New Features

1. Create new module in `js/`
2. Import in `index.html`
3. Initialize in app-multisite.js

### Custom Themes

1. Override CSS variables
2. Add to site configuration
3. Apply dynamically

## Monitoring & Debugging

### Debug Mode

Enable via URL:
```
?debug=1
```

### Console Commands

```javascript
// Check configuration
window.ImagesDebug.config

// Test image loading
window.ImagesDebug.test.pickUrl({src: 'test.jpg'})

// View current site
window.currentSite

// Enable logging
window.Log.setEnabled(true)
```

### Performance Monitoring

```javascript
// Measure load time
performance.mark('app-start');
// ... application loads
performance.mark('app-ready');
performance.measure('app-load', 'app-start', 'app-ready');
```

## Future Enhancements

### Planned Features

1. **PWA Support**
   - Service worker for offline access
   - App manifest for installation

2. **Advanced Analytics**
   - User interaction tracking
   - Performance metrics
   - Error reporting

3. **Enhanced Media**
   - Video backgrounds
   - 3D property tours
   - Interactive maps

4. **API Integration**
   - Real-time availability
   - Dynamic pricing
   - Lead capture

5. **Accessibility**
   - ARIA improvements
   - Keyboard navigation
   - Screen reader optimization

### Architecture Evolution

```
Current: Static Site
    ↓
Phase 2: JAMstack with API
    ↓
Phase 3: Full-stack Application
```

## Best Practices

### Code Organization

1. One module per file
2. Clear naming conventions
3. Documented public APIs
4. Consistent error handling

### Performance

1. Minimize HTTP requests
2. Optimize asset sizes
3. Use browser caching
4. Lazy load when possible

### Maintenance

1. Keep dependencies minimal
2. Document configuration changes
3. Version control everything
4. Test before deploying

### Security

1. No credentials in code
2. Validate all inputs
3. Use HTTPS always
4. Regular security audits