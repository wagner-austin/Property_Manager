# 🏗️ Property Manager

Modern property marketing system for real estate developments with automated Google Drive integration.

## ✨ Features

- **📁 Google Drive Integration** - Automatic document syncing and management
- **🏘️ Multi-Site Support** - Each property gets its own configuration
- **📱 Responsive Design** - Mobile-first PDF viewer with smooth navigation  
- **🎨 Professional UI** - Clean design optimized for real estate marketing
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
├── sites/              # Site-specific data
│   └── lancaster-12/   # Lancaster property (12 lots)
├── scripts/            # Python automation tools  
├── js/                 # Frontend JavaScript
├── css/                # Styles
├── config/             # Configuration files
└── Makefile            # Build commands
```

## 🛠️ Development

```bash
# Run linters and formatters
make lint

# Audit Drive files
make drive-audit

# Update site data with Drive IDs
make drive-apply SITE=lancaster-12

# Create deployment package
make pack
```

## 📝 Configuration

1. **Google Drive Setup**
   - Place credentials in `config/credentials.json`
   - Run `python -m scripts.setup_drive_api`

2. **Site Configuration**
   - Edit `config/settings.json` for folder IDs
   - Each site has its own `sites/[name]/data.json`

## 🔧 Tech Stack

- **Frontend**: Vanilla JavaScript, CSS Grid, HTML5
- **Backend**: Python scripts for Drive API
- **Build**: Make, ESLint, Prettier, Black, Ruff
- **Deploy**: Static site compatible

## 📦 Deployment

The site can be deployed to any static hosting service:

- GitHub Pages
- Netlify  
- Vercel
- AWS S3
- Traditional web hosting

## 📄 About

**Huntington Beach Capital Partners, Inc.**  
Rick Reza / President  
16882 Bolsa Chica St. #102  
Huntington Beach, CA 92649  
Phone: (714) 713-8618  
DRE. 00970335 NMLS. 273226

---

Property Manager System • Maintained by Austin Wagner