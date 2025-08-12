# Lancaster 12 Lots - Marketing Website

Professional single-page website for showcasing 12 premium development lots in Lancaster, CA.

## 🚀 Quick Start

1. **Upload PDFs to Google Drive**
   - Upload all property PDFs to Google Drive
   - Right-click each → "Get link" → Set to "Anyone with the link can view"
   - Copy the share links

2. **Update `data.js`**
   - Open `data.js` in any text editor
   - Replace `FILE_ID_OR_SHARE_URL` placeholders with your Drive share links
   - You can paste either the full URL or just the ID

3. **Test Locally**
   - Open `index.html` in any browser
   - All "Coming Soon" buttons will activate once Drive links are added

4. **Deploy**
   - Upload all 4 files to your hosting service:
     - `index.html`
     - `styles.css`
     - `app.js`
     - `data.js`
   - **Note**: OG image must be an absolute URL on your domain
   - Popular free hosts: GitHub Pages, Netlify, Vercel

## 📁 File Mapping

Update these in `data.js`:

### Main Presentation
- `presentation.file` → `AA 1 LANCASTER 12 PRESENTATION.pdf`

### Project Documents
- Tentative Map → `LANCASTER 12 LOT TENTATIVE MAP.pdf`
- Entitlements → `LANCASTER 12 ENTITLEMENTS.pdf`
- Grading Plan → `LANCASTER Conceptual Grading Plan 03202025 (1).pdf`
- LLC Info → `LANCASTER 43741 LLC INFO.pdf`
- Verella Court → `VERELLA COURT Prelim - 7278395 (2).pdf`
- Duke July → `LANCASTER 12 DUKE JULY.pdf`

### Home Plans
- Plan 1 → `LANCASTER PLAN 1 PLANS.pdf`
- Plan 2 → `LANCASTER PLAN 2 PLANS.pdf`
- Plan 3 → `LANCASTER PLAN 3 PLANS.pdf`
- Plan 4 → `LANCASTER PLAN 4.pdf` (rename from PLAN #4)
- Desert Crest → `DESERT CREST HOMES PLAN I.pdf`

### Individual Lots
- Option 1: Link each lot to its specific documentation
- Option 2: Link all to main PDF with `page: X` for deep-linking

## ⚠️ Important Notes

1. **File Naming**: Remove `#` from filenames before uploading (e.g., `PLAN #4` → `PLAN 4`)
2. **Spelling**: Fix "TENATIVE" → "TENTATIVE" in file names
3. **Permissions**: All Drive files must be set to "Anyone with link can view"
4. **Photos**: Add lot photos by setting the `photo` property in each lot object

## 🎨 Features

- **Responsive Design**: Works on all devices
- **PDF Viewer**: In-page Drive preview with "Open in New Tab" option
- **Accessibility**: ARIA labels, keyboard navigation, focus management
- **SEO Ready**: Open Graph tags for social sharing
- **Print Friendly**: Clean print styles included
- **Data Validation**: Console warnings for missing Drive links

## 📞 Contact

**Huntington Beach Capital Partners, Inc.**
- Phone: 714-713-8618
- Email: rickreza@yahoo.com
- Drive Folder: [View All Files](https://drive.google.com/drive/folders/1iXsOCeIYZAK3DGknFOYZENNATpyavLW-)

## 🛠️ Customization

### Add Lot Photos
```javascript
// In data.js, add photo URLs:
{ 
  number: "Lot 1",
  photo: "https://your-image-url.jpg",
  // ... rest of lot data
}
```

### Change Colors
Edit CSS variables in `styles.css`:
```css
:root {
  --primary: #1a365d;     /* Navy blue */
  --accent: #2563eb;      /* Bright blue */
  --success: #10b981;     /* Green */
}
```

### Add OG Image
Replace placeholder in `index.html`:
```html
<meta property="og:image" content="https://your-domain.com/og-image.jpg">
```

## 🚨 Troubleshooting

### Drive Preview Issues
- **Page jumps not working**: Drive preview sometimes ignores `#page=N`. Options:
  1. Split PDFs into individual lot files
  2. Use "Open in Drive" link and navigate manually

### Network Restrictions  
- **Preview blocked**: Corporate networks may block Drive iframes
- **Solution**: Use the "Open in Drive" button in the modal viewer

## 🌐 Hosting Tips

### Netlify Drop (Instant Deploy)
1. Go to [app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag folder containing all 4 files
3. Get instant public URL

### GitHub Pages
1. Create new repository
2. Push all files to main branch
3. Settings → Pages → Deploy from `/root`
4. Site available at `https://[username].github.io/[repo-name]/`

## 🔒 Security Notes

- All external links use `rel="noopener noreferrer"` for security
- Phone links use international format: `tel:+17147138618`
- Drive files require "Anyone with link" permission

## ✅ Deployment Checklist

- [ ] Rename `LANCASTER PLAN #4.pdf` → `LANCASTER PLAN 4.pdf`
- [ ] Fix spelling: "TENATIVE" → "TENTATIVE" 
- [ ] Upload all PDFs to Google Drive
- [ ] Set all files to "Anyone with link can view"
- [ ] Copy share links into `data.js`
- [ ] Test site locally in browser
- [ ] Check console for validation warnings
- [ ] Deploy to hosting service
- [ ] Test live site on mobile and desktop
- [ ] Share link with clients!