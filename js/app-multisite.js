// ==========================================
// Multi-Site Property Marketing Application
// ==========================================

// Acquire logger from window with a safe fallback
const Log =
  typeof window !== 'undefined' && window.Log
    ? window.Log
    : {
        debug() {},
        info() {},
        warn() {},
        error() {},
        group() {},
        groupEnd() {},
      };

// --- Multi-site loader ---
async function loadSiteData() {
  const params = new URLSearchParams(location.search);
  const rawSlug = params.get('site') || 'lancaster-12';
  const slug = /^[a-z0-9._-]+$/i.test(rawSlug) ? rawSlug : 'lancaster-12'; // sanitize

  // Log if slug was sanitized
  if (rawSlug !== slug) {
    window.Log && Log.event('site.param.sanitized', { raw: rawSlug, slug });
  }

  window.Log && Log.event('site.loading', { slug });

  // Try loading from sites directory first
  try {
    window.Log && Log.time('fetch-site-data');
    const res = await fetch(`sites/${slug}/data.json`, { cache: 'no-store' });
    if (res.ok) {
      const json = await res.json();
      window.Log && Log.timeEnd('fetch-site-data');
      const cfg = normalizeConfig(json);
      window.Log &&
        Log.event('site.loaded', {
          slug,
          source: 'json',
          counts: {
            docs: (cfg.projectDocs || []).length,
            plans: (cfg.plans || []).length,
            lots: (cfg.lots || []).length,
          },
        });
      return cfg;
    } else {
      window.Log && Log.timeEnd('fetch-site-data');
      window.Log &&
        Log.event('site.load.http_error', {
          slug,
          status: res.status,
          statusText: res.statusText,
        });
    }
  } catch {
    window.Log && Log.timeEnd('fetch-site-data');
    window.Log && Log.log(`No data.json found for ${slug}`);
  }

  window.Log && Log.event('site.load.failed', { slug });
  throw new Error(`Could not load site data for slug "${slug}"`);
}

// --- Drive ID extraction ---
function extractDriveId(input) {
  if (!input) return null;
  const s = String(input).trim();

  // Skip placeholders
  if (s === 'FILE_ID_OR_URL' || s === 'PASTE_FILE_ID_HERE') {
    return null;
  }

  // Already a Drive ID
  if (/^[-\w]{10,}$/.test(s)) {
    return s;
  }

  // Extract from various Drive URL formats
  const patterns = [/\/d\/([-\w]{10,})/, /[?&#]id=([-\w]{10,})/, /\/file\/d\/([-\w]{10,})/];

  for (const pattern of patterns) {
    const match = s.match(pattern);
    if (match) return match[1];
  }

  return null;
}

// --- Normalize configuration ---
function normalizeConfig(cfg) {
  const norm = JSON.parse(JSON.stringify(cfg)); // Deep clone

  // Helper to normalize file references
  const normalizeFile = (obj) => {
    if (!obj) return obj;

    // Handle different property names for files
    if (obj.file) {
      obj.fileId = extractDriveId(obj.file);
    } else if (obj.documentID) {
      obj.fileId = extractDriveId(obj.documentID);
    }

    return obj;
  };

  // Normalize all file references
  normalizeFile(norm.presentation);
  (norm.lots || []).forEach(normalizeFile);
  (norm.plans || []).forEach(normalizeFile);
  (norm.projectDocs || []).forEach(normalizeFile);

  // Ensure required fields exist
  norm.viewer = norm.viewer || 'drive';
  norm.brand = norm.brand || {};
  norm.contact = norm.contact || {};
  norm.location = norm.location || {};
  norm.drive = norm.drive || {};

  return norm;
}

// --- PDF helpers ------------------------------------------------------------
function isGoogleDrive(urlOrId) {
  if (!urlOrId) return false;
  if (/^[\w-]{25,}$/.test(urlOrId)) return true; // looks like a Drive file id
  try {
    const u = new URL(urlOrId, location.href);
    return u.hostname.includes('drive.google.com');
  } catch {
    return false;
  }
}

function localPdfUrl(urlOrPath) {
  // Return a same-origin absolute URL if it's local, else null
  if (!urlOrPath) return null;
  try {
    const u = new URL(urlOrPath, location.href);
    return u.origin === location.origin ? u.href : null;
  } catch {
    // relative path -> assume local
    return new URL(urlOrPath, location.href).href;
  }
}

function _driveViewUrl(idOrUrl) {
  // Fallback to full Drive tab (shows all controls); don't iframe it.
  let id = idOrUrl;
  try {
    const u = new URL(idOrUrl, location.href);
    const m = u.pathname.match(/\/d\/([^/]+)/);
    if (m) id = m[1];
  } catch {
    // Invalid URL, treat as ID
  }
  if (/^[\w-]{25,}$/.test(id)) {
    return `https://drive.google.com/file/d/${id}/view`;
  }
  return null;
}

function drivePreviewUrl(fileIdOrUrl, _page) {
  const id = extractDriveId(fileIdOrUrl);
  if (!id) return null;

  // Use preview with rm=minimal for cleaner embed
  return `https://drive.google.com/file/d/${id}/preview`;
}

function directPdfUrl(id, page) {
  // Direct download URL - bypasses Drive UI and CSP restrictions
  return `https://drive.google.com/uc?export=download&id=${id}${page ? `#page=${page}` : ''}`;
}

function pdfjsPreviewUrl(fileIdOrUrl, page) {
  const id = extractDriveId(fileIdOrUrl);
  const fileUrl = id ? `https://drive.google.com/uc?export=download&id=${id}` : fileIdOrUrl;

  const pageHash = page ? `#page=${page}` : '';
  // Use relative path for PDF.js to work under subpaths
  return `vendor/pdfjs/web/viewer.html?file=${encodeURIComponent(fileUrl)}${pageHash}`;
}

// Get appropriate preview URL based on viewer setting
function getPreviewUrl(site, fileIdOrUrl, page) {
  const s = String(fileIdOrUrl || '');
  const isHttp = /^https?:\/\//i.test(s);
  const id = extractDriveId(s);
  const viewer = (site.viewer || 'drive').toLowerCase();

  // If we have a Drive ID
  if (id) {
    if (viewer === 'direct') return directPdfUrl(id, page);
    if (viewer === 'pdfjs') return pdfjsPreviewUrl(s, page);
    // Default: Drive preview
    return drivePreviewUrl(s, page);
  }

  // Non-Drive URL
  if (isHttp) {
    return viewer === 'pdfjs' ? pdfjsPreviewUrl(s, page) : s;
  }

  return null;
}

// --- Theme application ---
function applyTheme(site) {
  const theme = site?.brand?.theme;
  if (!theme) return;

  const root = document.documentElement.style;
  if (theme.primary) root.setProperty('--primary', theme.primary);
  if (theme.accent) root.setProperty('--accent', theme.accent);
  if (theme.success) root.setProperty('--success', theme.success);
  if (theme.border) root.setProperty('--border', theme.border);
  if (theme.textDark) root.setProperty('--text-dark', theme.textDark);
  if (theme.textLight) root.setProperty('--text-light', theme.textLight);
}

// --- Update page content ---
function updatePageContent(site) {
  // Update brand
  if (site.brand?.title) {
    document.title = site.brand.title;
    const h1 = document.querySelector('h1');
    if (h1) h1.textContent = site.brand.title;
  }

  if (site.brand?.tagline) {
    const tagline = document.querySelector('.tagline');
    if (tagline) tagline.textContent = site.brand.tagline;
  }

  // Update hero bullets
  if (site.heroBullets?.length) {
    const bulletsContainer = document.querySelector('.hero-bullets');
    if (bulletsContainer) {
      bulletsContainer.innerHTML = site.heroBullets
        .map((bullet) => `<div class="hero-bullet">${bullet}</div>`)
        .join('');
    }
  }

  // Update contact info
  if (site.contact) {
    const c = site.contact;

    // Company name
    const companyEls = document.querySelectorAll('#companyName, #footerCompany');
    companyEls.forEach((el) => {
      if (el && c.companyName) el.textContent = c.companyName;
    });

    // Phone - support both formats
    const rawPhone = c.phoneE164 || c.phone || '';
    const phoneDisplay = c.phoneDisplay || rawPhone;

    if (rawPhone && phoneDisplay) {
      document.querySelectorAll('#phoneLink, #mobilePhone').forEach((link) => {
        if (!link) return;
        const digits = rawPhone.replace(/[^\d+0-9]/g, '');
        const e164 = digits.startsWith('+') ? digits : `+1${digits.replace(/^1/, '')}`;
        link.href = `tel:${e164}`;
        link.textContent = phoneDisplay;
      });
    }

    // Email
    if (c.email) {
      const emailLinks = document.querySelectorAll('#emailLink, #mobileEmail');
      emailLinks.forEach((link) => {
        if (link) {
          link.href = `mailto:${c.email}`;
          link.textContent = c.email;
        }
      });
    }
  }
}

// --- PDF Modal ---
let _lastFocusedElement = null;
let _modalKeyHandler = null;
let _modalFocusTrap = null;
let _modalBackdropHandler = null;
let __pdfObsSetup = false;
let __pdfSrcObserver = null;

// --- PDF Modal Observability ---
function setupPDFObservability() {
  if (__pdfObsSetup) return;
  __pdfObsSetup = true;

  const pdfModal = document.getElementById('pdfModal');
  const pdfFrame = document.getElementById('pdfFrame');
  const pdfNewTab = document.getElementById('pdfNewTab');

  let lastSrc = '';
  let frameLoadStart = 0;

  // Detect "open" when src changes
  if (pdfFrame) {
    __pdfSrcObserver = new MutationObserver(() => {
      const src = pdfFrame.getAttribute('src') || '';
      if (src && src !== lastSrc) {
        lastSrc = src;
        frameLoadStart = window.performance ? performance.now() : Date.now();

        // Comprehensive Drive URL pattern matching
        let id = null;
        let page = null;

        // Try various Drive URL patterns
        const patterns = [
          /\/d\/([^/]+)\/preview(?:#page=(\d+))?/, // /preview pattern
          /\/d\/([^/]+)\/view(?:#page=(\d+))?/, // /view pattern
          /[?&]id=([^&#]+)(?:.*#page=(\d+))?/, // uc?id= pattern
          /\/file\/d\/([^/]+)(?:.*#page=(\d+))?/, // /file/d/ pattern
        ];

        for (const pattern of patterns) {
          const match = src.match(pattern);
          if (match) {
            id = match[1];
            page = match[2] ? Number(match[2]) : null;
            break;
          }
        }

        window.Log &&
          Log.event('pdf.frame.src_changed', {
            id,
            page,
            hasSrc: !!src,
            isDrive: !!id,
          });
      } else if (!src && lastSrc) {
        // Frame cleared (modal closing)
        lastSrc = '';
        window.Log && Log.event('pdf.frame.cleared');
      }
    });
    __pdfSrcObserver.observe(pdfFrame, { attributes: true, attributeFilter: ['src'] });

    // Track frame load completion
    pdfFrame.addEventListener('load', () => {
      if (frameLoadStart) {
        const loadTime = (window.performance ? performance.now() : Date.now()) - frameLoadStart;
        window.Log &&
          Log.event('pdf.frame.loaded', {
            loadTimeMs: Math.round(loadTime),
          });
        frameLoadStart = 0;
      }
    });
  }

  // Track "Open in new tab" clicks
  if (pdfNewTab && !pdfNewTab.dataset.logHooked) {
    pdfNewTab.addEventListener('click', (_e) => {
      window.Log &&
        Log.event('pdf.new_tab_clicked', {
          href: pdfNewTab.href,
        });
    });
    pdfNewTab.dataset.logHooked = '1';
  }

  // Track escape key specifically for modal
  document.addEventListener('keydown', (e) => {
    if (
      e.key === 'Escape' &&
      pdfModal &&
      (pdfModal.classList.contains('active') || pdfModal.classList.contains('open'))
    ) {
      window.Log && Log.event('pdf.escape_pressed');
    }
  });
}

// --- Modal open/close with clean history -----------------
let pdfModalOpen = false;

function openPDF(site, fileRef, title, page) {
  // For compatibility with existing code that passes site as first param
  let fileIdOrUrl = fileRef;
  let docTitle = title || 'Floor Plan';

  // Check if this is a Google Drive file
  const isDrive = isGoogleDrive(fileIdOrUrl);

  if (isDrive) {
    // Use Drive preview URL for iframe embedding
    const driveUrl = drivePreviewUrl(fileIdOrUrl, page);
    if (!driveUrl) {
      alert('Document not yet available. Please check back later.');
      return;
    }

    // Build modal lazily
    const modal = document.querySelector('.c-modal.pdf') || buildPdfModal();
    const frame = modal.querySelector('.c-modal__frame');
    const headerTitle = modal.querySelector('.c-modal__title');

    headerTitle.textContent = docTitle;
    frame.src = driveUrl;

    // Open modal
    modal.setAttribute('open', '');
    document.body.classList.add('modal-open');
    pdfModalOpen = true;

    // Add a hash to track modal state
    if (!window.location.hash || window.location.hash !== '#pdf-modal') {
      window.location.hash = 'pdf-modal';
    }

    frame.focus();
    return;
  }

  // For local files, check if we have a valid URL
  const localUrl = localPdfUrl(fileIdOrUrl);

  if (!localUrl) {
    // Fallback to getPreviewUrl for compatibility
    const previewUrl = getPreviewUrl(site, fileRef, page);
    if (!previewUrl) {
      window.Log && Log.event('pdf.open.failed', { title: docTitle, reason: 'no_url' });
      alert('Document not yet available. Please check back later.');
      return;
    }
    fileIdOrUrl = previewUrl;
  }

  // Build modal lazily
  const modal = document.querySelector('.c-modal.pdf') || buildPdfModal();
  const frame = modal.querySelector('.c-modal__frame');
  const headerTitle = modal.querySelector('.c-modal__title');

  const finalUrl = localUrl || fileIdOrUrl;

  headerTitle.textContent = docTitle;
  // Use native viewer for local PDFs, fit to width
  // view=FitH is the standard parameter for horizontal fit
  frame.src = `${finalUrl}#view=FitH`;

  // Open
  modal.setAttribute('open', '');
  document.body.classList.add('modal-open');
  pdfModalOpen = true;

  // Add a hash to track modal state
  if (!window.location.hash || window.location.hash !== '#pdf-modal') {
    window.location.hash = 'pdf-modal';
  }

  frame.focus();
}

function buildPdfModal() {
  const modal = document.createElement('div');
  modal.className = 'c-modal pdf c-modal--xl';
  modal.innerHTML = `
    <div class="c-modal__panel" role="dialog" aria-modal="true" aria-label="Floor plan">
      <div class="c-modal__header">
        <h3 class="c-modal__title">Floor Plan</h3>
        <div class="c-modal__actions">
          <button class="c-btn c-btn--primary c-btn--sm c-modal__newtab" aria-label="Open in new tab">Open in New Tab</button>
          <button class="c-modal__close" aria-label="Close">✕</button>
        </div>
      </div>
      <div class="c-modal__body">
        <iframe class="c-modal__frame" title="PDF viewer" allow="fullscreen"></iframe>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Close handlers (single path)
  const closeBtn = modal.querySelector('.c-modal__close');
  closeBtn.addEventListener('click', () => closePDF('button'));

  // New tab handler
  const newTabBtn = modal.querySelector('.c-modal__newtab');
  newTabBtn.addEventListener('click', () => {
    const frame = modal.querySelector('.c-modal__frame');
    if (frame && frame.src) {
      // Check if this is a Google Drive preview URL
      if (frame.src.includes('drive.google.com') && frame.src.includes('/preview')) {
        // Convert preview URL to view URL for better experience
        const viewUrl = frame.src.replace('/preview', '/view');
        window.open(viewUrl, '_blank', 'noopener');
      } else {
        // For local PDFs, just remove the view parameters
        const cleanUrl = frame.src.replace(/#.*$/, '');
        window.open(cleanUrl, '_blank', 'noopener');
      }
    }
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closePDF('backdrop');
  });
  document.addEventListener('keydown', (e) => {
    if (pdfModalOpen && (e.key === 'Escape' || e.key === 'Backspace')) {
      e.preventDefault();
      closePDF(e.key === 'Escape' ? 'esc' : 'backspace');
    }
  });

  return modal;
}

function closePDF(_via = 'unknown') {
  const modal = document.querySelector('.c-modal.pdf');
  if (!modal || !modal.hasAttribute('open')) return;

  // Close the modal immediately
  document.body.classList.remove('modal-open');
  modal.removeAttribute('open');
  const frame = modal.querySelector('.c-modal__frame');
  if (frame) frame.src = 'about:blank';
  pdfModalOpen = false;

  // Remove hash if it's still there
  if (window.location.hash === '#pdf-modal') {
    // Go back to remove the hash
    if (_via === 'back' || _via === 'popstate') {
      // Hash will be removed by the back navigation itself
    } else {
      // For other close methods, remove hash without adding to history
      history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }
}

// Drive folder modal - embed the folder view directly
function openDriveModal() {
  // Create modal if it doesn't exist
  let modal = document.querySelector('.drive-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.className = 'c-modal drive-modal c-modal--xl';
    modal.innerHTML = `
      <div class="c-modal__panel" role="dialog" aria-modal="true">
        <div class="c-modal__header">
          <h3 class="c-modal__title">All Properties & Documents</h3>
          <div class="c-modal__actions">
            <button class="c-btn c-btn--primary c-btn--sm" onclick="window.open('https://drive.google.com/drive/folders/1_cSGSHD-JK0HnrydV_PPzKuSoIrMDEk5', '_blank')">Open in Google Drive</button>
            <button class="c-modal__close" aria-label="Close">✕</button>
          </div>
        </div>
        <div class="c-modal__body">
          <iframe 
            class="c-modal__frame" 
            src="https://drive.google.com/drive/folders/1_cSGSHD-JK0HnrydV_PPzKuSoIrMDEk5"
            title="Document Library" 
            allow="fullscreen"
            style="width: 100%; height: 100%; border: 0;">
          </iframe>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Close button handler
    modal.querySelector('.c-modal__close').addEventListener('click', closeDriveModal);

    // Backdrop click handler
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeDriveModal();
    });

    // ESC key handler
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.hasAttribute('open')) {
        closeDriveModal();
      }
    });
  }

  // Open modal
  modal.setAttribute('open', '');
  document.body.classList.add('modal-open');
}

function closeDriveModal() {
  const modal = document.querySelector('.drive-modal');
  if (modal) {
    modal.removeAttribute('open');
    document.body.classList.remove('modal-open');
    // Clear iframe to stop any loading
    const frame = modal.querySelector('.c-modal__frame');
    if (frame) frame.src = 'about:blank';
  }
}

// Make functions globally available
window.openDriveModal = openDriveModal;
window.closeDriveModal = closeDriveModal;

// Image expansion modal
function openImageModal(imageSrc, title) {
  // Create a simple fullscreen image modal
  const modal = document.createElement('div');
  modal.className = 'image-expand-modal';
  modal.innerHTML = `
    <div class="image-expand-content">
      <button class="image-expand-close" aria-label="Close image">✕</button>
      <img src="${imageSrc}" alt="${title}" />
      <div class="image-expand-title">${title}</div>
    </div>
  `;

  // Add styles
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.9);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: zoom-out;
    animation: fadeIn 0.3s ease;
  `;

  const content = modal.querySelector('.image-expand-content');
  content.style.cssText = `
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  `;

  const img = modal.querySelector('img');
  img.style.cssText = `
    max-width: 100%;
    max-height: calc(90vh - 60px);
    object-fit: contain;
  `;

  const closeBtn = modal.querySelector('.image-expand-close');
  closeBtn.style.cssText = `
    position: absolute;
    top: -40px;
    right: 0;
    background: transparent;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    padding: 10px;
    z-index: 1;
  `;

  const titleDiv = modal.querySelector('.image-expand-title');
  titleDiv.style.cssText = `
    color: white;
    margin-top: 20px;
    font-size: 1.2rem;
    text-align: center;
  `;

  // Close handlers
  const closeModal = () => {
    modal.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => modal.remove(), 300);
  };

  closeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    closeModal();
  });

  modal.addEventListener('click', closeModal);

  content.addEventListener('click', (e) => e.stopPropagation());

  // ESC key handler
  const escHandler = (e) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);

  document.body.appendChild(modal);
}

// --- Render functions ---
function renderLots(site) {
  const container = document.getElementById('lotsGrid');
  if (!container || !site.lots) return;

  container.innerHTML = '';

  site.lots.forEach((lot) => {
    const card = document.createElement('article');
    card.className = 'c-card c-card--clickable';
    card.setAttribute('data-variant', 'lot');

    // Add photos if available
    if (lot.photos?.length) {
      const figure = document.createElement('figure');
      figure.className = 'c-card__media';

      const img = document.createElement('img');
      const firstPhoto = lot.photos[0];
      img.src = typeof firstPhoto === 'string' ? firstPhoto : firstPhoto.src;
      img.alt =
        typeof firstPhoto === 'string'
          ? `${lot.number} photo`
          : firstPhoto.alt || `${lot.number} photo`;
      img.loading = 'lazy';
      img.decoding = 'async';
      img.fetchPriority = 'low';

      figure.appendChild(img);
      card.appendChild(figure);
    }

    const content = document.createElement('div');
    content.innerHTML = `
      <div class="c-card__header">
        <div class="c-card__title">${lot.title || lot.number}</div>
        ${lot.size ? `<div class="c-card__meta">${lot.size}</div>` : ''}
      </div>
      <div class="c-card__body">
        ${lot.description ? `<p>${lot.description}</p>` : ''}
        ${
          Array.isArray(lot.features) && lot.features.length
            ? `
          <ul class="c-card__features">
            ${lot.features.map((f) => `<li>${f}</li>`).join('')}
          </ul>`
            : ''
        }
      </div>
      <div class="c-card__actions">
        <button class="c-btn c-btn--primary">View Lot Documents</button>
      </div>
    `;

    card.appendChild(content);

    const button = card.querySelector('button');
    button.type = 'button';
    button.setAttribute('aria-label', `View documents for ${lot.title || `Lot ${lot.number}`}`);

    // Prefer title_report if present, else fallback to the lot's file/platmap
    const ref =
      (lot.docRefs &&
        (lot.docRefs.title_report || lot.docRefs.grading || lot.docRefs.plan_assignment)) ||
      lot.file ||
      lot.fileId;
    const canOpen = !!getPreviewUrl(site, ref, lot.page);

    button.disabled = !canOpen;
    if (!canOpen) {
      button.textContent = 'Coming Soon';
      button.setAttribute('aria-disabled', 'true');
    } else {
      button.textContent = 'View Lot Documents';
      // Make the whole card clickable for better UX
      const open = () => openPDF(site, ref, lot.title || lot.number, lot.page);
      button.addEventListener('click', open);

      card.addEventListener('click', (e) => {
        if (e.target.closest('button')) return; // don't double-trigger
        open();
      });
    }

    container.appendChild(card);
  });
}

function renderPresentation(site) {
  const container = document.getElementById('presentationContainer');
  if (!container) return;

  container.innerHTML = '';

  // Find the presentation in projectDocs
  const presentation = (site.projectDocs || []).find((doc) => doc.id === 'presentation');
  if (!presentation) return;

  const card = document.createElement('div');
  card.className = 'c-card';
  card.setAttribute('data-variant', 'plan');

  const refDoc = presentation.file || presentation.fileId;
  const canOpenDoc = !!getPreviewUrl(site, refDoc, presentation.page);

  // Use the presentation first page image
  const presentationImage = 'public/brand/logos/FIRST PAGE OF CREST PRESENTATION.png';

  card.innerHTML = `
    ${
      presentationImage
        ? `
      <div class="c-card__media" style="cursor: pointer;">
        <img src="${presentationImage}" alt="${presentation.title}" loading="lazy" />
      </div>
    `
        : ''
    }
    <div class="c-card__body">
      ${!presentationImage ? `<div class="c-card__icon">${presentation.icon || '📊'}</div>` : ''}
      <h3 class="c-card__title">${presentation.title}</h3>
      ${presentation.description ? `<p class="c-card__description">${presentation.description}</p>` : ''}
    </div>
    <div class="c-card__actions">
      <button class="c-btn c-btn--primary" aria-label="View ${presentation.title} PDF">
        View Presentation
      </button>
    </div>
  `;

  // Add click handler for image to open PDF (same as button)
  if (presentationImage && canOpenDoc) {
    const imageDiv = card.querySelector('.c-card__media');
    if (imageDiv) {
      imageDiv.addEventListener('click', () => {
        openPDF(site, refDoc, presentation.title, presentation.page);
      });
    }
  }

  const button = card.querySelector('button');
  button.type = 'button';
  button.disabled = !canOpenDoc;

  if (!canOpenDoc) {
    button.textContent = 'Coming Soon';
    button.setAttribute('aria-disabled', 'true');
  } else {
    button.addEventListener('click', () => {
      openPDF(site, refDoc, presentation.title, presentation.page);
    });
  }

  container.appendChild(card);
}

function renderPlans(site) {
  const container = document.getElementById('plansGrid');
  if (!container || !site.plans) return;

  container.innerHTML = '';

  site.plans.forEach((plan, _index) => {
    const card = document.createElement('div');
    card.className = 'c-card';
    card.setAttribute('data-variant', 'plan');

    // Map plan names to PNG images
    const planImageMap = {
      'Plan 1': 'public/images/lancaster plans/plan-1.png',
      'Plan 2': 'public/images/lancaster plans/plan-2.png',
      'Plan 3': 'public/images/lancaster plans/plan-3.png',
      'Plan 4': 'public/images/lancaster plans/plan-4.png',
    };

    const planImage = planImageMap[plan.name];

    card.innerHTML = `
      ${
        planImage
          ? `
        <div class="c-card__media" style="cursor: pointer;" title="Click to enlarge">
          <img src="${planImage}" alt="${plan.title}" loading="lazy" />
        </div>
      `
          : ''
      }
      <div class="c-card__body">
        ${!planImage ? `<div class="c-card__icon">${plan.icon || '🏠'}</div>` : ''}
        <h3 class="c-card__title">${plan.title}</h3>
        <ul class="c-card__features">
          <li>${plan.sqft.toLocaleString()} Square Feet</li>
          <li>${plan.bedrooms} ${plan.bedrooms === 1 ? 'Bedroom' : 'Bedrooms'}</li>
          <li>${plan.bathrooms} ${plan.bathrooms === 1 ? 'Bathroom' : 'Bathrooms'}</li>
          ${plan.garage ? `<li>${plan.garage} Car Garage</li>` : ''}
        </ul>
      </div>
      <div class="c-card__actions">
        <button class="c-btn c-btn--primary" aria-label="View ${plan.title} PDF">
          Review Working Plans
        </button>
      </div>
    `;

    // Add click handler for image expansion
    if (planImage) {
      const imageDiv = card.querySelector('.c-card__media');
      if (imageDiv) {
        imageDiv.addEventListener('click', () => {
          openImageModal(planImage, plan.title);
        });
      }
    }

    const button = card.querySelector('button');
    button.type = 'button';

    const refPlan = plan.file || plan.fileId;
    const canOpenPlan = !!getPreviewUrl(site, refPlan, plan.page);

    button.disabled = !canOpenPlan;
    if (!canOpenPlan) {
      button.textContent = 'Coming Soon';
      button.setAttribute('aria-disabled', 'true');
    } else {
      button.textContent = 'Review Working Plans';
      button.addEventListener('click', () => {
        openPDF(site, refPlan, plan.title, plan.page);
      });
    }

    container.appendChild(card);
  });

  // Add the two documentation cards as plan cards
  const docs = (site.projectDocs || []).filter(
    (doc) => doc.id === 'entitlement-report' || doc.id === 'tract-grading'
  );

  docs.forEach((doc) => {
    const card = document.createElement('div');
    const isEntitlement = doc.id === 'entitlement-report';
    card.className = isEntitlement
      ? 'c-card c-card--doc c-card--entitlement'
      : 'c-card c-card--doc';
    card.setAttribute('data-variant', 'plan');

    const refDoc = doc.file || doc.fileId;
    const canOpenDoc = !!getPreviewUrl(site, refDoc, doc.page);

    // For Entitlement Report, use a preview image of the PDF first page
    const previewImage = isEntitlement ? 'public/documents/entitlement-preview.png' : null;

    if (isEntitlement && previewImage) {
      // Full PDF preview style for Entitlement Report
      card.innerHTML = `
        <div class="c-card__media" style="position: relative; padding: 0 12px 45px 12px; background: white;">
          <img src="${previewImage}" alt="${doc.title}" loading="lazy" style="width: 100%; height: 100%; object-fit: contain; position: relative; top: -8px;" />
          <div class="c-card__actions" style="position: absolute; bottom: 0; left: 0; right: 0; background: rgba(255, 255, 255, 0.95); margin: 0;">
            <button class="c-btn c-btn--primary" aria-label="View ${doc.title} PDF">
              View Document
            </button>
          </div>
        </div>
      `;
    } else {
      // Regular style for other docs
      const isTractGrading = doc.id === 'tract-grading';
      card.innerHTML = `
        <div class="c-card__body" style="${isTractGrading ? 'cursor: pointer; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 250px; padding-bottom: 40px;' : ''}">
          <div class="c-card__icon" style="${isTractGrading ? 'font-size: 3rem;' : ''}">${doc.icon || '📄'}</div>
          <h3 class="c-card__title" style="${isTractGrading ? 'font-size: 1.3rem; text-align: center;' : ''}">${doc.title}</h3>
          ${doc.description ? `<p class="c-card__description">${doc.description}</p>` : ''}
        </div>
        <div class="c-card__actions">
          <button class="c-btn c-btn--primary" aria-label="View ${doc.title} PDF">
            View Document
          </button>
        </div>
      `;
    }

    if (isEntitlement && previewImage) {
      // For Entitlement Report, handle button click
      const button = card.querySelector('button');
      if (button) {
        button.type = 'button';
        button.disabled = !canOpenDoc;

        if (!canOpenDoc) {
          button.textContent = 'Coming Soon';
          button.setAttribute('aria-disabled', 'true');
        } else {
          button.addEventListener('click', () => {
            openPDF(site, refDoc, doc.title, doc.page);
          });
        }
      }

      // Also make the image clickable
      const img = card.querySelector('.c-card__media img');
      if (img && canOpenDoc) {
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => {
          openPDF(site, refDoc, doc.title, doc.page);
        });
      }
    } else {
      // For other docs, use the button
      const button = card.querySelector('button');
      if (button) {
        button.type = 'button';
        button.disabled = !canOpenDoc;

        if (!canOpenDoc) {
          button.textContent = 'Coming Soon';
          button.setAttribute('aria-disabled', 'true');
        } else {
          button.addEventListener('click', () => {
            openPDF(site, refDoc, doc.title, doc.page);
          });

          // For tract-grading card, make the entire card clickable
          if (doc.id === 'tract-grading') {
            const cardBody = card.querySelector('.c-card__body');
            if (cardBody) {
              cardBody.addEventListener('click', () => {
                openPDF(site, refDoc, doc.title, doc.page);
              });
            }
          }
        }
      }
    }

    container.appendChild(card);
  });
}

function renderDocuments(site) {
  const container = document.getElementById('documentsGrid');
  if (!container) return;

  container.innerHTML = '';

  // Add project documents (excluding presentation which is now in plans section)
  (site.projectDocs || []).forEach((doc) => {
    if (doc.id !== 'presentation') {
      container.appendChild(createDocCard(site, doc));
    }
  });
}

function createDocCard(site, doc) {
  const card = document.createElement('div');
  card.className = 'c-card';
  card.setAttribute('data-variant', 'doc');

  const refDoc = doc.file || doc.fileId;
  const canOpenDoc = !!getPreviewUrl(site, refDoc, doc.page);

  card.innerHTML = `
    <div class="c-card__body">
      <div class="c-card__icon">${doc.icon || '📄'}</div>
      <h4 class="c-card__title">${doc.title}</h4>
      ${doc.description ? `<p>${doc.description}</p>` : ''}
    </div>
    <div class="c-card__actions">
      <button type="button" class="c-btn c-btn--primary" aria-label="View ${doc.title}">
        ${canOpenDoc ? 'View Document' : 'Coming Soon'}
      </button>
    </div>
  `;

  const viewBtn = card.querySelector('.c-btn');
  viewBtn.type = 'button';

  if (canOpenDoc) {
    viewBtn.addEventListener('click', () => {
      window.Log && Log.event('doc.view.clicked', { title: doc.title });
      openPDF(site, refDoc, doc.title, doc.page);
    });
  } else {
    viewBtn.classList.add('disabled');
    viewBtn.setAttribute('aria-disabled', 'true');
    viewBtn.disabled = true;
  }

  return card;
}

// --- Data validation ---
function validateSiteData(site) {
  const missing = [];

  if (!site.brand?.title) missing.push('brand.title');
  if (!site.contact?.companyName) missing.push('contact.companyName');

  let fileCount = 0;
  let missingCount = 0;

  // Check presentation
  if (site.presentation) {
    fileCount++;
    if (!site.presentation.fileId) missingCount++;
  }

  // Check lots
  (site.lots || []).forEach((lot, _i) => {
    fileCount++;
    if (!lot.fileId) missingCount++;
  });

  // Check plans
  (site.plans || []).forEach((plan, _i) => {
    fileCount++;
    if (!plan.fileId) missingCount++;
  });

  // Check docs
  (site.projectDocs || []).forEach((doc, _i) => {
    fileCount++;
    if (!doc.fileId) missingCount++;
  });

  if (missingCount > 0) {
    console.warn(`⚠️ ${missingCount}/${fileCount} documents missing Drive IDs`);
  } else if (fileCount > 0) {
    Log.info(`✅ All ${fileCount} documents have Drive IDs`);
  }

  return { missing, fileCount, missingCount };
}

// --- Initialize application ---
async function initApp() {
  try {
    // Load site data
    const site = await loadSiteData();
    window.SITE = site; // Store globally for debugging

    Log.info(`Loaded site: ${site.slug || 'default'}`);

    // Validate data
    validateSiteData(site);

    // Apply theme
    applyTheme(site);

    // Update page content
    updatePageContent(site);

    // Render sections
    renderLots(site);
    renderPresentation(site);
    renderPlans(site);
    renderDocuments(site);

    // Set up modal close handler
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => closePDF('button'));
    }

    // Set up PDF modal observability
    setupPDFObservability();

    // Smooth scrolling for hash links only
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href') || '';
        // Only handle real in-page hashes; skip modal links and marked elements
        if (
          href.startsWith('#') &&
          href !== '#' &&
          !this.closest('.pdf-modal') &&
          !this.dataset.noScroll
        ) {
          e.preventDefault();
          try {
            const target = document.querySelector(href);
            if (target) {
              target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          } catch {
            // Invalid selector, just navigate normally
          }
        }
      });
    });

    // Clean up observer on page unload
    window.addEventListener('beforeunload', () => {
      if (__pdfSrcObserver) {
        __pdfSrcObserver.disconnect();
        __pdfSrcObserver = null;
      }
    });
  } catch (error) {
    console.error('Failed to initialize app:', error);
    document.body.innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <h2>Error Loading Property Data</h2>
        <p>${error.message}</p>
        <p>Please check the URL or contact support.</p>
      </div>
    `;
  }
}

// Handle hash changes (including back button)
window.addEventListener('hashchange', () => {
  // If we're navigating away from #pdf-modal, close the modal
  if (window.location.hash !== '#pdf-modal' && pdfModalOpen) {
    closePDF('back');
  }
});

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
