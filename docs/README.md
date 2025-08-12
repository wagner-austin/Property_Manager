# Property Manager - Multi-Site Real Estate Platform

Professional property marketing system with Google Drive integration for real estate developments.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ 
- Node.js 16+ (for linting)
- Google Drive API credentials

### Initial Setup

```bash
# Install dependencies
make setup

# Configure Google Drive API
python -m scripts.setup_drive_api

# Start local server
make serve
# Or with debug logging
make debug
```

## 📁 Project Structure

```
Property_Manager/
├── index.html              # Main entry point
├── sites/                  # Site-specific configurations
│   └── lancaster-12/       # Example property
│       └── data.json       # Site configuration & Drive IDs
├── js/                     # Frontend JavaScript
│   ├── app-multisite.js    # Main application logic
│   └── logger.js           # Debug logging system
├── css/                    # Stylesheets
│   └── styles.css          # Main styles
├── scripts/                # Python automation tools
│   ├── audit_drive_files.py      # Audit Drive folder structure
│   ├── generate_url_template.py  # Create URL mapping template
│   ├── update_site_data.py       # Update site with Drive IDs
│   └── setup_drive_api.py        # Configure Google API access
├── config/                 # Configuration files
│   └── settings.json       # Global settings
└── Makefile               # Build & development commands
```

## 🛠️ Development Workflow

### 1. Audit Your Drive Files
```bash
# Check what files are in your Drive folder
make drive-audit

# Or specify a folder
python -m scripts.audit_drive_files --folder YOUR_FOLDER_ID
```

### 2. Generate URL Template
```bash
# Create a template for mapping files to IDs
make urls
```

### 3. Update Site Data
```bash
# Apply Drive IDs to your site configuration
make drive-apply SITE=lancaster-12
```

### 4. Test Locally
```bash
# Start development server
make serve

# View at: http://localhost:8000/?site=lancaster-12
```

### 5. Run Linters
```bash
# Check code quality
make lint
```

## 📦 Deployment

### GitHub Pages (Recommended)
1. Push to GitHub
2. Go to Settings → Pages
3. Source: Deploy from branch → main → / (root)
4. Site available at: `https://[username].github.io/[repo]/`

### Other Platforms
- **Netlify**: Drag & drop deployment
- **Vercel**: Connect GitHub repo
- **Traditional hosting**: Upload all files via FTP

## 🎨 Features

- **Multi-Site Support**: Each property has its own configuration
- **Google Drive Integration**: Automatic PDF management
- **Responsive Design**: Mobile-first approach
- **Debug Mode**: Built-in logging system (`?debug=1`)
- **SEO Ready**: Open Graph tags for social sharing
- **Static Site**: No backend required

## 📝 Configuration

### Site Configuration
Edit `sites/[site-name]/data.json`:
- Company information
- Contact details  
- Drive folder IDs
- Property details
- Document mappings

### Global Settings
Edit `config/settings.json`:
- Default site
- API credentials paths
- Global folder IDs

## 🔧 Make Commands

```bash
make help          # Show all commands
make setup         # Install dependencies
make serve         # Start local server
make debug         # Start with debug logging
make lint          # Run all linters
make drive-audit   # Audit Drive files
make urls          # Generate URL template
make drive-apply   # Update site with Drive IDs
make pack          # Create deployment package
make clean         # Remove generated files
```

## 📞 Support

**Huntington Beach Capital Partners, Inc.**
- Phone: 714-713-8618
- Email: rickreza@yahoo.com

---

Created by Austin Wagner • Property Marketing Platform