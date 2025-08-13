# 🚀 Deployment Guide

## Prerequisites
✅ Drive IDs configured in `sites/[site-name]/data.json`
✅ Images configured in `config/images.json`
✅ Test locally with `make serve`
✅ All linting passing with `make lint`
✅ Images optimized and in `public/` directory

## Create Deployment Package

```bash
# Create deployment.zip with all necessary files
make pack

# Or manually specify output
make pack OUT=my-site.zip
```

### What's Included
- All HTML, CSS, JS files
- `public/` directory with images
- `sites/` directory with configurations
- `config/` directory
- No Python scripts or credentials

## Deployment Options

### 1️⃣ GitHub Pages (Recommended - FREE)

#### Setup (One Time)
1. Push code to GitHub repository
2. Go to **Settings** → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main** → **/ (root)**
5. Click **Save**

#### Your Site URL
```
https://[username].github.io/[repository-name]/
```

Example: `https://wagner-austin.github.io/Property_Manager/`

#### Updates
- Simply push to main branch
- Site updates automatically in ~2-5 minutes

### 2️⃣ Netlify (Easy Drag & Drop)

#### No Account Needed
1. Go to [app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag your `deployment.zip` onto the page
3. Get instant URL like `amazing-wilson-abc123.netlify.app`

#### With Account (Free)
1. Sign up at [netlify.com](https://netlify.com)
2. Connect GitHub repository
3. Auto-deploys on every push
4. Custom domain support

### 3️⃣ Vercel (Fast Global CDN)

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Import repository
4. Automatic deploys on every push
5. Excellent performance analytics

### 4️⃣ Traditional Hosting (cPanel/FTP)

1. Extract `deployment.zip`
2. Upload all files via FTP to:
   - `public_html/` (root domain)
   - `public_html/properties/` (subdirectory)
3. Ensure `index.html` is in the root
4. Set folder permissions to 755

### 5️⃣ AWS S3 + CloudFront

```bash
# Upload to S3
aws s3 sync . s3://your-bucket-name --exclude ".*" --exclude "node_modules/*"

# Enable static website hosting
aws s3 website s3://your-bucket-name --index-document index.html

# Optional: Add CloudFront for CDN
```

## Custom Domain Setup

### For GitHub Pages
1. Create `CNAME` file with your domain
2. Configure DNS:
   - A record: `185.199.108.153`
   - A record: `185.199.109.153`
   - A record: `185.199.110.153`
   - A record: `185.199.111.153`
   - CNAME: `www` → `[username].github.io`

### For Netlify/Vercel
1. Add custom domain in dashboard
2. Follow their DNS configuration guide
3. Automatic SSL certificates

## Verify Deployment

### Quick Checks
- ✅ Homepage loads
- ✅ Owner photo and logos display
- ✅ Background images load
- ✅ PDF viewer opens
- ✅ Mobile responsive
- ✅ Contact links work
- ✅ Drive folder button links correctly

### Debug Mode
Add `?debug=1` to URL and check browser console:
```
https://your-site.com/?site=lancaster-12&debug=1
```

## Troubleshooting

### PDFs Not Loading
- Check Drive permissions (must be "Anyone with link")
- Verify file IDs in `sites/[site]/data.json`
- Check browser console for errors

### Images Not Loading
- Verify paths in `config/images.json` start with `/public/`
- Check file names match exactly (case-sensitive)
- Ensure images are included in deployment package
- Test with `?debugImages=1` for detailed logging

### Site Not Updating
- GitHub Pages: Wait 5-10 minutes
- Clear browser cache (Ctrl+Shift+R)
- Check GitHub Actions tab for build errors

### 404 Errors
- Ensure all file paths are relative
- Check case sensitivity (especially on Linux hosts)
- Verify `.htaccess` if using Apache

## Environment Variables

For advanced deployments, set these in your hosting platform:

```bash
# Optional: Override default site
DEFAULT_SITE=lancaster-12

# Optional: Google Analytics
GA_TRACKING_ID=UA-XXXXXXXXX-X
```

---

Need help? Contact: rickreza@yahoo.com