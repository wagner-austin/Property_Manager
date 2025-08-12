# 🚀 Deployment Guide

## Prerequisites
✅ Add your Google Drive file IDs to `js/data.js`
✅ Test locally with `scripts/test-server.bat` (Windows) or `scripts/test-server.sh` (Mac/Linux)

## Create Deployment Package

### Windows
```cmd
scripts\create-deployment.bat
```

### Mac/Linux
```bash
chmod +x scripts/create-deployment.sh
./scripts/create-deployment.sh

# Or with custom name:
./scripts/create-deployment.sh lancaster-site.zip
```

## Deploy Options

### 1️⃣ Netlify Drop (Easiest - No Account Needed)
1. Go to [app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag `deployment.zip` onto the page
3. Get instant URL like `amazing-wilson-abc123.netlify.app`
4. Optional: Create free account to customize URL

### 2️⃣ GitHub Pages (Free with Custom Domain)
1. Create new GitHub repository
2. Extract `deployment.zip`
3. Push files to `main` branch
4. Go to Settings → Pages → Deploy from branch → main
5. Site available at `https://[username].github.io/[repo-name]/`

### 3️⃣ Vercel (Fast Global CDN)
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Drag `deployment.zip` or connect repo
4. Automatic deploys on every push

### 4️⃣ Traditional Hosting (cPanel, FTP)
1. Extract `deployment.zip`
2. Upload contents via FTP to `public_html/` or `www/`
3. Ensure `index.html` is in root

## Verify Deployment

After deploying, check:
- [ ] Homepage loads
- [ ] Console has no errors (F12 → Console)
- [ ] Click a document - modal opens
- [ ] "Open in Drive" links work
- [ ] Mobile responsive (resize browser)
- [ ] Contact links work

## Custom Domain Setup

### Netlify
1. Site Settings → Domain Management → Add custom domain
2. Add CNAME record: `www` → `[your-site].netlify.app`
3. Add A record: `@` → `75.2.60.5`

### GitHub Pages
1. Settings → Pages → Custom domain
2. Add CNAME record: `www` → `[username].github.io`
3. Enable "Enforce HTTPS"

## Troubleshooting

**Drive preview not loading?**
- Check Drive files are set to "Anyone with link can view"
- Try "Open in Drive" button as fallback

**404 errors?**
- Ensure all files from `deployment.zip` were uploaded
- Check file paths are lowercase (some servers are case-sensitive)

**Mobile issues?**
- Clear browser cache
- Test in incognito/private mode

## Update Content

1. Edit `js/data.js` with new Drive links
2. Re-run deployment script
3. Upload new `deployment.zip`
4. Changes appear immediately (may need to clear cache)