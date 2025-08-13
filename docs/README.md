# Property Manager Documentation

Comprehensive documentation for the Property Manager multi-site real estate platform.

## 📚 Documentation Index

### Getting Started
- [Setup Guide](SETUP-GUIDE.md) - Initial setup and configuration
- [Quick Start](#quick-start) - Get up and running quickly
- [Browser Support](BROWSER-SUPPORT.md) - Compatibility information

### Configuration
- [Configuration Guide](CONFIGURATION.md) - All configuration options
- [Smart Mapper](SMART-MAPPER.md) - Intelligent file categorization
- [Image System](IMAGE-SYSTEM.md) - Image management documentation

### Development
- [Architecture Overview](ARCHITECTURE.md) - System design and patterns
- [API Reference](API-REFERENCE.md) - JavaScript and Python APIs
- [Multi-Site Guide](MULTISITE-GUIDE.md) - Managing multiple properties

### Deployment
- [Deployment Guide](DEPLOY.md) - Hosting and deployment options

## 🚀 Quick Start

See [Setup Guide](SETUP-GUIDE.md) for detailed installation instructions.

```bash
# Quick setup
make deps               # Install dependencies
make serve              # Start local server
# Visit: http://localhost:8000/?site=lancaster-12
```

For complete project structure, see [Architecture Overview](ARCHITECTURE.md).

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

See [Deployment Guide](DEPLOY.md) for detailed hosting instructions.

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
Edit `sites.config.json`:
- Default site
- API credentials paths
- Global folder IDs

## 🔧 Make Commands

### Development

```bash
make help          # Show all commands
make deps          # Install dependencies
make serve         # Start local server
make debug         # Start with debug logging
make lint          # Run all linters
make drive-audit   # Audit Drive files
make urls          # Generate URL template
make drive-apply   # Update site with Drive IDs
make pack          # Create deployment package
make clean         # Remove generated files
```

## 📚 Additional Resources

### Documentation Files

| Document | Description |
|----------|-------------|
| [SETUP-GUIDE.md](SETUP-GUIDE.md) | Complete setup instructions |
| [CONFIGURATION.md](CONFIGURATION.md) | Configuration reference |
| [IMAGE-SYSTEM.md](IMAGE-SYSTEM.md) | Image management system |
| [API-REFERENCE.md](API-REFERENCE.md) | API documentation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| [SMART-MAPPER.md](SMART-MAPPER.md) | Smart mapper documentation |
| [MULTISITE-GUIDE.md](MULTISITE-GUIDE.md) | Multi-site management |
| [DEPLOY.md](DEPLOY.md) | Deployment instructions |
| [BROWSER-SUPPORT.md](BROWSER-SUPPORT.md) | Browser compatibility |

### Key Features

- **Local Image Management** - Owner photos, logos, backgrounds
- **Google Drive Integration** - Automatic document syncing
- **Smart File Mapping** - Pattern recognition for categorization
- **Completeness Tracking** - Document availability monitoring
- **Multi-Site Support** - Multiple properties from one codebase
- **Responsive Design** - Mobile-first approach
- **Beach Theme** - Professional design with custom colors
- **Debug Mode** - Built-in development tools
- **Static Deployment** - Works anywhere

## 📞 Support

**Huntington Beach Capital Partners, Inc.**
- Phone: 714-713-8618
- Email: rickreza@yahoo.com

---

Property Manager • Created by Austin Wagner