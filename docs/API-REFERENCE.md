# API Reference

## JavaScript Modules

### `js/app-multisite.js`

The main application module that handles multi-site functionality and rendering.

#### Global Functions

##### `loadSiteData(siteSlug)`
Loads configuration data for a specific site.

```javascript
const siteData = await loadSiteData('lancaster-12');
```

**Parameters:**
- `siteSlug` (string): The site identifier

**Returns:**
- Promise<Object>: Site configuration data

##### `renderSite(data)`
Renders the complete site based on configuration data.

```javascript
await renderSite(siteData);
```

**Parameters:**
- `data` (Object): Site configuration object

##### `renderLots(lots)`
Renders the lots grid section.

```javascript
renderLots(data.lots);
```

**Parameters:**
- `lots` (Array): Array of lot objects

##### `renderPlans(plans)`
Renders the home plans section.

```javascript
renderPlans(data.plans);
```

**Parameters:**
- `plans` (Array): Array of plan objects

##### `renderDocuments(documents)`
Renders the project documents section.

```javascript
renderDocuments(data.projectDocs);
```

**Parameters:**
- `documents` (Array): Array of document objects

#### Event Handlers

##### `openPDF(fileId, title, page)`
Opens a PDF in the modal viewer.

```javascript
openPDF('DRIVE_FILE_ID', 'Document Title', 5);
```

**Parameters:**
- `fileId` (string): Google Drive file ID or URL
- `title` (string): Document title for display
- `page` (number, optional): Page number to jump to

**Behavior:**
- Adds `#pdf-modal` hash to URL for back button handling
- Can be closed with ESC key, back button (mobile), or X button

##### `closePDF()`
Closes the PDF modal viewer.

```javascript
closePDF();
```

**Behavior:**
- Removes modal from view
- Clears iframe source
- Removes `#pdf-modal` hash from URL

#### Custom Events

##### `lots:rendered`
Fired when lots have been rendered to the DOM.

```javascript
window.addEventListener('lots:rendered', () => {
  console.log('Lots rendered');
});
```

---

### `js/images.js`

Dynamic image loading and management system.

#### Configuration

##### Image Configuration Object
```javascript
{
  owner: {
    photo: {
      src: string,      // Image URL or path
      srcId: string,    // Google Drive ID (optional)
      alt: string,      // Alt text
      caption: string,  // Caption text
      loading: string,  // 'eager' | 'lazy'
      display: boolean  // Show/hide control
    }
  },
  logos: {
    header: {...},
    footer: {...}
  },
  backgrounds: {
    hero: {
      image: string,
      overlay: string,
      position: string,
      size: string,
      attachment: string,
      enabled: boolean
    }
  }
}
```

#### Utility Functions

##### `extractDriveId(url)`
Extracts Google Drive ID from various URL formats.

```javascript
const id = extractDriveId('https://drive.google.com/file/d/ABC123/view');
// Returns: 'ABC123'
```

##### `toDrive(idOrUrl)`
Converts Drive ID to direct view URL.

```javascript
const url = toDrive('ABC123');
// Returns: 'https://drive.google.com/uc?export=view&id=ABC123'
```

##### `pickUrl(config, placeholder)`
Selects the appropriate URL from configuration.

```javascript
const url = pickUrl({src: '/image.jpg'}, '/placeholder.svg');
```

##### `setImg(element, config, placeholder)`
Applies image configuration to an IMG element.

```javascript
setImg(document.getElementById('logo'), logoConfig, placeholderUrl);
```

##### `applyBg(element, config, fallback)`
Applies background configuration to an element.

```javascript
applyBg(headerElement, backgroundConfig, fallbackUrl);
```

#### Debug Interface

##### `window.ImagesDebug`
Debug object for troubleshooting image loading.

```javascript
window.ImagesDebug = {
  config: Object,     // Current configuration
  elements: Object,   // DOM element references
  test: {
    toDrive: Function,
    pickUrl: Function
  }
}
```

---

### `js/logger.js`

Logging system with debug support.

#### Logger API

##### `Log.debug(...args)`
Logs debug-level messages.

```javascript
Log.debug('Debug message', {data: value});
```

##### `Log.info(...args)`
Logs info-level messages.

```javascript
Log.info('Operation completed');
```

##### `Log.warn(...args)`
Logs warning messages.

```javascript
Log.warn('Potential issue detected');
```

##### `Log.error(...args)`
Logs error messages.

```javascript
Log.error('Operation failed', error);
```

##### `Log.withPrefix(prefix)`
Creates a logger with a prefix.

```javascript
const logger = Log.withPrefix('[Images]');
logger.info('Loading images'); // Output: [Images] Loading images
```

##### `Log.setEnabled(enabled)`
Enables or disables logging.

```javascript
Log.setEnabled(true);  // Enable logging
Log.setEnabled(false); // Disable logging
```

##### `Log.setLevel(level)`
Sets the minimum log level.

```javascript
Log.setLevel('debug'); // Show all messages
Log.setLevel('warn');  // Show warnings and errors only
```

---

## Python Scripts

### `scripts/smart_site_mapper.py`

Intelligent file categorization and site data generation.

#### Command Line Usage

```bash
python scripts/smart_site_mapper.py [options]
```

**Options:**
- `--config PATH`: Configuration file path (default: `sites.config.json`)
- `--inventory PATH`: Drive inventory file (default: `file-mapping.json`)
- `--sites-dir PATH`: Output directory (default: `sites`)
- `--dry-run`: Preview without writing files

#### Main Functions

##### `SiteMapper.__init__(config_path, inventory_path, sites_dir)`
Initializes the mapper with configuration.

##### `SiteMapper.process_all_sites()`
Processes all sites in configuration.

##### `SiteMapper.process_site(site_config, files)`
Processes a single site's files.

##### `SiteMapper.categorize_file(filename)`
Categorizes a file based on patterns.

**Returns:**
```python
{
  'category': str,  # 'plan', 'lot', 'document', 'misc'
  'number': int,    # Plan/lot number if applicable
  'doc_type': str,  # Document type if applicable
  'score': float    # Match confidence (0-100)
}
```

---

### `scripts/audit_drive_files.py`

Audits Google Drive folder structure.

#### Command Line Usage

```bash
python scripts/audit_drive_files.py --folder FOLDER_ID [options]
```

**Options:**
- `--folder ID`: Google Drive folder ID to audit
- `--output PATH`: Output file path (default: `file-mapping.json`)
- `--credentials PATH`: Credentials file path
- `--verbose`: Enable verbose output

#### Main Functions

##### `audit_folder(folder_id, credentials_path)`
Audits a Drive folder and returns file listing.

**Returns:**
```python
{
  'folder_id': str,
  'folder_name': str,
  'files': [
    {
      'id': str,
      'name': str,
      'mimeType': str,
      'size': int,
      'modifiedTime': str
    }
  ]
}
```

---

### `scripts/setup_drive_api.py`

Sets up Google Drive API authentication.

#### Command Line Usage

```bash
python scripts/setup_drive_api.py
```

Guides through OAuth2 authentication flow and saves credentials.

---

## Configuration Files

### `sites.config.json`

Site configuration with lot tracking and requirements.

#### Schema

```json
{
  "global": {
    "default_bedrooms": number,
    "default_bathrooms": number,
    "default_sqft": number,
    "strict_mode": boolean,
    "max_misc_docs": number
  },
  "sites": [
    {
      "slug": string,
      "name": string,
      "aliases": string[],
      "drive_folder_id": string,
      "lot_count": number,
      "lot_details": {
        "[lot_number]": {
          "apn": string,
          "address": string,
          "status": string,
          "size": string,
          "has_title_report": boolean,
          "has_grading": boolean,
          "has_plan_assignment": boolean,
          "doc_refs": object
        }
      },
      "lot_requirements": {
        "show_missing": boolean,
        "hide_incomplete": boolean,
        "required_docs": string[],
        "show_status_in_size": boolean
      },
      "plan_details": {
        "[plan_number]": {
          "bedrooms": number,
          "bathrooms": number,
          "sqft": number,
          "stories": number,
          "garage_sf": number
        }
      },
      "document_overrides": {
        "[doc_type]": {
          "title": string,
          "description": string,
          "hide": boolean
        }
      }
    }
  ]
}
```

### `config/images.json`

Image asset configuration.

#### Schema

```json
{
  "owner": {
    "photo": {
      "src": string,
      "alt": string,
      "caption": string,
      "loading": "eager" | "lazy",
      "display": boolean
    }
  },
  "logos": {
    "header": {
      "src": string,
      "alt": string,
      "width": number,
      "loading": "eager" | "lazy",
      "display": boolean
    },
    "footer": {
      "src": string,
      "alt": string,
      "width": number,
      "display": boolean
    }
  },
  "backgrounds": {
    "hero": {
      "image": string,
      "overlay": string,
      "position": string,
      "size": string,
      "attachment": string,
      "enabled": boolean
    },
    "sections": {
      "[section_name]": {
        "imageId": string,
        "overlay": string,
        "enabled": boolean
      }
    }
  },
  "placeholders": {
    "owner": string,
    "logo": string,
    "lot": string,
    "background": string
  }
}
```

---

## URL Parameters

### Site Selection

```
?site=lancaster-12
```

Loads a specific site configuration.

### Debug Mode

```
?debug=1
```

Enables debug logging in console.

### Combined

```
?site=lancaster-12&debug=1
```

---

## CSS Custom Properties

### Theme Colors

```css
:root {
  --brand-ocean-900: #003d5b;
  --brand-ocean-700: #0a5071;
  --brand-ocean-500: #2a7299;
  --brand-sand-200: #f4e4c1;
  --brand-sand-300: #e8d5a7;
  --brand-sand-400: #d4b896;
  --foam-white: #fefefe;
  --sky-light: #e3f2fd;
}
```

### Dynamic Properties

```css
/* Set by JavaScript */
--hero-image: url(...);
--hero-overlay: linear-gradient(...);
--hero-position: center center;
--hero-size: cover;
--hero-attachment: fixed;
```

---

## Browser APIs Used

- **Fetch API**: Loading JSON configurations
- **MutationObserver**: Watching for DOM changes
- **URLSearchParams**: Parsing query strings
- **CustomEvent**: Custom event dispatching
- **IntersectionObserver**: (Future) Lazy loading
- **matchMedia**: Dark mode detection

---

## Error Handling

### Image Loading Errors

```javascript
el.onerror = () => {
  logger.error('IMG load FAILED', {
    element: el.id,
    src: el.src
  });
  // Fallback to placeholder
  el.src = placeholderUrl;
};
```

### Configuration Errors

```javascript
if (!cfg) {
  logger.error('No configuration loaded');
  return;
}
```

### Network Errors

```javascript
try {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
} catch (error) {
  logger.error('Failed to load', error);
  // Use fallback
}
```