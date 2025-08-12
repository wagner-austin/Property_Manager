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
    window.Log && Log.log(`No data.json found for ${slug}, trying legacy format...`);
  }

  // Fallback to legacy window.DATA if available
  if (window.DATA) {
    window.Log && Log.log('Using legacy window.DATA format');
    const cfg = normalizeConfig(window.DATA);
    window.Log &&
      Log.event('site.loaded', {
        slug,
        source: 'legacy',
        counts: {
          docs: (cfg.projectDocs || []).length,
          plans: (cfg.plans || []).length,
          lots: (cfg.lots || []).length,
        },
      });
    return cfg;
  }

  // Try loading data.js script
  try {
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `sites/${slug}/data.js`;
      script.defer = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });

    if (window.DATA) {
      return normalizeConfig(window.DATA);
    }
  } catch (e) {
    window.Log && Log.error(`Failed to load data.js for ${slug}`, e);
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

// --- Preview URL generators ---
function drivePreviewUrl(fileIdOrUrl, page) {
  const id = extractDriveId(fileIdOrUrl);
  if (!id) return null;

  // Note: Drive preview ignores page parameter
  const pageHash = page ? `#page=${page}` : '';
  return `https://drive.google.com/file/d/${id}/preview${pageHash}`;
}

function driveViewUrl(fileIdOrUrl, page) {
  const id = extractDriveId(fileIdOrUrl);
  if (!id) return null;

  const pageHash = page ? `#page=${page}` : '';
  return `https://drive.google.com/file/d/${id}/view${pageHash}`;
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

  // Update Drive folder link - prefer Public over generic folder
  const folderId =
    site.drive?.publicFolderId ||
    site.drive?.folderId ||
    site.contact?.publicFolderId ||
    site.contact?.folderId;

  if (folderId) {
    const folderLink = document.getElementById('driveFolder');
    if (folderLink) {
      folderLink.href = `https://drive.google.com/drive/folders/${folderId}`;
      // harden external link
      folderLink.target = '_blank';
      folderLink.rel = 'noopener noreferrer';

      // Add click tracking (avoid duplicates)
      if (!folderLink.dataset.logHooked) {
        folderLink.addEventListener('click', () => {
          window.Log && Log.event('drive.folder.clicked', { folderId });
        });
        // Track middle-click / new-tab
        folderLink.addEventListener('auxclick', (e) => {
          if (e.button === 1) {
            window.Log && Log.event('drive.folder.auxclick', { folderId, button: e.button });
          }
        });
        folderLink.dataset.logHooked = '1';
      }

      window.Log && Log.event('drive.folder.linked', { folderId });
    }
  } else {
    // graceful fallback: keep users on-page instead of a dead link
    const folderLink = document.getElementById('driveFolder');
    if (folderLink) {
      folderLink.href = '#documents';
      window.Log && Log.log('No folder ID configured, linking to documents section');
    }
  }
}

// --- PDF Modal ---
let lastFocusedElement = null;
let modalKeyHandler = null;
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

function openPDF(site, fileRef, title, page) {
  // Get preview URL first - works with Drive IDs or external URLs
  let previewUrl = getPreviewUrl(site, fileRef, page);
  const viewUrl = driveViewUrl(fileRef, page) || (typeof fileRef === 'string' ? fileRef : null);

  if (!previewUrl) {
    window.Log && Log.event('pdf.open.failed', { title, reason: 'no_url' });
    alert('Document not yet available. Please check back later.');
    return;
  }

  // Only coerce to /preview when explicitly using the Drive viewer
  const viewer = (site.viewer || 'drive').toLowerCase();
  if (viewer === 'drive' && previewUrl && !/\/preview(?:$|[#?])/.test(previewUrl)) {
    const id = extractDriveId(fileRef);
    if (id) previewUrl = drivePreviewUrl(fileRef, page);
  }

  // Log PDF open event
  window.Log &&
    Log.event('pdf.open', {
      title,
      fileRef: typeof fileRef === 'string' ? fileRef : 'object',
      page: page || null,
    });

  lastFocusedElement = document.activeElement;

  const modal = document.getElementById('pdfModal');
  const frame = document.getElementById('pdfFrame');
  const titleEl = document.getElementById('pdfTitle');
  const newTabLink = document.getElementById('pdfNewTab');
  const closeBtn = document.getElementById('closeModal');

  titleEl.textContent = title || 'Document';
  frame.src = previewUrl;
  // "Open in new tab" can use /view for better UX
  if (viewUrl) {
    newTabLink.href = viewUrl;
    newTabLink.dataset.noScroll = '1'; // Opt out of smooth-scroll handler
  }

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Focus management
  const focusableElements = modal.querySelectorAll(
    'a[href], button:not([disabled]), [tabindex="0"]'
  );
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  modalKeyHandler = function (e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      closePDF('escape');
    }

    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      } else if (!e.shiftKey && document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }
  };

  modal.addEventListener('keydown', modalKeyHandler);
  setTimeout(() => closeBtn.focus(), 100);
}

function closePDF(via = 'unknown') {
  const modal = document.getElementById('pdfModal');
  const frame = document.getElementById('pdfFrame');
  const titleEl = document.getElementById('pdfTitle');

  // Log PDF close event
  window.Log &&
    Log.event('pdf.close', {
      title: titleEl ? titleEl.textContent : 'Unknown',
      via: via,
    });

  if (modalKeyHandler) {
    modal.removeEventListener('keydown', modalKeyHandler);
    modalKeyHandler = null;
  }

  modal.classList.remove('active');
  frame.src = '';
  document.body.style.overflow = '';

  if (lastFocusedElement) {
    lastFocusedElement.focus();
    lastFocusedElement = null;
  }
}

// --- Render functions ---
function renderLots(site) {
  const container = document.getElementById('lotsGrid');
  if (!container || !site.lots) return;

  container.innerHTML = '';

  site.lots.forEach((lot) => {
    const card = document.createElement('article');
    card.className = 'lot-card';

    // Add photos if available
    if (lot.photos?.length) {
      const figure = document.createElement('figure');
      figure.className = 'lot-img';

      const img = document.createElement('img');
      const firstPhoto = lot.photos[0];
      img.src = typeof firstPhoto === 'string' ? firstPhoto : firstPhoto.src;
      img.alt =
        typeof firstPhoto === 'string'
          ? `${lot.number} photo`
          : firstPhoto.alt || `${lot.number} photo`;
      img.loading = 'lazy';

      figure.appendChild(img);
      card.appendChild(figure);
    }

    const content = document.createElement('div');
    content.innerHTML = `
      <div class="lot-header">
        <div class="lot-number">${lot.title || lot.number}</div>
        <div class="lot-size">${lot.size || 'Size TBD'}</div>
      </div>
      ${lot.description ? `<p class="lot-description">${lot.description}</p>` : ''}
      <div class="lot-content">
        <ul class="lot-features">
          ${(lot.features || []).map((f) => `<li>${f}</li>`).join('')}
        </ul>
        <button class="btn">View Lot Documents</button>
      </div>
    `;

    card.appendChild(content);

    const button = card.querySelector('button');
    // Prefer title_report if present, else fallback to the lot's file/platmap
    const ref =
      (lot.docRefs &&
        (lot.docRefs.title_report || lot.docRefs.grading || lot.docRefs.plan_assignment)) ||
      lot.file ||
      lot.fileId;
    const canOpen = !!getPreviewUrl(site, ref, lot.page);

    button.disabled = !canOpen;
    button.textContent = canOpen ? 'View Lot Documents' : 'Coming Soon';
    if (canOpen) {
      button.addEventListener('click', () => {
        openPDF(site, ref, lot.title || lot.number, lot.page);
      });
    }

    container.appendChild(card);
  });
}

function renderPlans(site) {
  const container = document.getElementById('plansGrid');
  if (!container || !site.plans) return;

  container.innerHTML = '';

  site.plans.forEach((plan) => {
    const card = document.createElement('div');
    card.className = 'plan-card';

    card.innerHTML = `
      <div class="plan-header">
        <div class="plan-icon">${plan.icon || '🏠'}</div>
        <h3 class="plan-title">${plan.title}</h3>
        ${plan.description ? `<p class="plan-description">${plan.description}</p>` : ''}
      </div>
      <div class="plan-content">
        <button class="btn" aria-label="View ${plan.title} PDF">
          View Floor Plan
        </button>
      </div>
    `;

    const button = card.querySelector('button');
    const refPlan = plan.file || plan.fileId;
    const canOpenPlan = !!getPreviewUrl(site, refPlan, plan.page);

    button.disabled = !canOpenPlan;
    button.textContent = canOpenPlan ? 'View Floor Plan' : 'Coming Soon';
    if (canOpenPlan) {
      button.addEventListener('click', () => {
        openPDF(site, refPlan, plan.title, plan.page);
      });
    }

    container.appendChild(card);
  });
}

function renderDocuments(site) {
  const container = document.getElementById('documentsGrid');
  if (!container) return;

  container.innerHTML = '';

  // Add presentation first if it exists
  if (site.presentation && (site.presentation.file || site.presentation.fileId)) {
    container.appendChild(createDocCard(site, site.presentation));
  }

  // Add project documents
  (site.projectDocs || []).forEach((doc) => {
    container.appendChild(createDocCard(site, doc));
  });
}

function createDocCard(site, doc) {
  const card = document.createElement('div');
  card.className = 'doc-card';

  const refDoc = doc.file || doc.fileId;
  const canOpenDoc = !!getPreviewUrl(site, refDoc, doc.page);

  card.innerHTML = `
    <div class="doc-icon">${doc.icon || '📄'}</div>
    <h4 class="doc-title">${doc.title}</h4>
    <p class="doc-description">${doc.description || ''}</p>
    <div class="doc-actions">
      <button type="button" class="doc-link doc-link-view" aria-label="View ${doc.title}">
        ${canOpenDoc ? 'View Document' : 'Coming Soon'}
      </button>
    </div>
  `;

  const viewBtn = card.querySelector('.doc-link-view');
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
    console.log(`✅ All ${fileCount} documents have Drive IDs`);
  }

  return { missing, fileCount, missingCount };
}

// --- Initialize application ---
async function initApp() {
  try {
    // Load site data
    const site = await loadSiteData();
    window.SITE = site; // Store globally for debugging

    console.log(`Loaded site: ${site.slug || 'default'}`);

    // Validate data
    validateSiteData(site);

    // Apply theme
    applyTheme(site);

    // Update page content
    updatePageContent(site);

    // Render sections
    renderLots(site);
    renderPlans(site);
    renderDocuments(site);

    // Set up modal close handler
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => closePDF('button'));
    }

    // Set up PDF modal observability
    setupPDFObservability();

    // Global escape key handler
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const modal = document.getElementById('pdfModal');
        if (modal && (modal.classList.contains('active') || modal.classList.contains('open'))) {
          closePDF('escape');
        }
      }
    });

    // Background click to close modal
    const modal = document.getElementById('pdfModal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closePDF('background');
        }
      });
    }

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
          } catch (err) {
            // Invalid selector, just navigate normally
            Log.error('Invalid selector for smooth scroll:', href, err);
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

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
