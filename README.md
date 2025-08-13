# 🏗️ Property Manager

Modern property marketing system for real estate developments with integrated image management and automated Google Drive document handling.

## ✨ Features

- **🖼️ Local Image Management** - Integrated owner photos, logos, and custom backgrounds
- **📁 Google Drive Integration** - Automatic document syncing and management
- **🤖 Smart File Mapping** - Intelligent pattern recognition for plans, lots, and documents
- **📊 Completeness Tracking** - Monitor document availability per lot (title reports, grading, etc.)
- **🏘️ Multi-Site Support** - Each property gets its own configuration
- **📱 Responsive Design** - Mobile-first PDF viewer with smooth navigation  
- **🎨 Professional UI** - Beach-themed design with customizable brand colors
- **🔍 Debug Mode** - Built-in development insights and logging
- **🚀 Static Deployment** - Works on GitHub Pages, Netlify, or any static host

## 🚀 Quick Start

```bash
# Setup environment
make setup

# Configure Google Drive credentials
python -m scripts.setup_drive_api

# Start local server
make serve

# Or debug mode
make debug
```

## 📂 Project Structure

```
Property_Manager/
├── public/             # Local images and assets
│   ├── backgrounds/    # Background images
│   └── brand/          # Logos and owner photos
├── sites/              # Site-specific data
│   └── lancaster-12/   # Lancaster property (12 lots)
├── scripts/            # Python automation tools
│   ├── smart_site_mapper.py  # Intelligent file categorization
│   └── audit_drive_files.py  # Drive inventory generation
├── config/             # Configuration files
│   └── images.json     # Image configuration
├── sites.config.json   # Site configurations with lot tracking
├── js/                 # Frontend JavaScript
│   ├── app-multisite.js # Multi-site application logic
│   ├── images.js       # Image loading system
│   └── logger.js       # Debug logging
├── css/                # Styles
│   └── styles.css      # Beach-themed styles
├── docs/               # Documentation
└── Makefile            # Build commands
```

## 🛠️ Development

```bash
make lint               # Run linters and formatters
make drive-audit        # Audit Drive files  
make map                # Run smart mapper
make pack               # Create deployment package
```

For detailed development workflow, see [docs/README.md](docs/README.md).

## 📝 Configuration

- **Images**: `config/images.json` - Logos, photos, backgrounds
- **Sites**: `sites.config.json` - Property configurations
- **Data**: `sites/[name]/data.json` - Site-specific data

For complete configuration guide, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 🔧 Tech Stack

- **Frontend**: Vanilla JavaScript, CSS Grid, HTML5
- **Backend**: Python scripts for Drive API
- **Image System**: Dynamic loading with fallback support
- **Theming**: Beach-inspired color palette with CSS custom properties
- **Build**: Make, ESLint, Prettier, Black, Ruff
- **Deploy**: Static site compatible with any hosting provider

## 📦 Deployment

The site can be deployed to any static hosting service. See [docs/DEPLOY.md](docs/DEPLOY.md) for detailed instructions.

## 📄 About

**Huntington Beach Capital Partners, Inc.**  
Rick Reza / President  
16882 Bolsa Chica St. #102  
Huntington Beach, CA 92649  
Phone: (714) 713-8618  
DRE. 00970335 NMLS. 273226

---

## 📚 Documentation

For comprehensive documentation, see the [docs/](docs/) directory:
- [Quick Reference](docs/QUICK-REFERENCE.md) - Common tasks and commands
- [Configuration Guide](docs/CONFIGURATION.md) - All configuration options
- [Image System](docs/IMAGE-SYSTEM.md) - Image management documentation
- [API Reference](docs/API-REFERENCE.md) - JavaScript and Python APIs
- [Architecture](docs/ARCHITECTURE.md) - System design and patterns

Property Manager System • Maintained by Austin Wagner