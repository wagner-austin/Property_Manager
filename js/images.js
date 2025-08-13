(async function () {
  // Use existing logger with prefix
  const logger = window.Log?.withPrefix('[Images]') || {
    debug: (...a) => console.log('[Images]', ...a),
    info: (...a) => console.log('[Images]', ...a),
    warn: (...a) => console.warn('[Images]', ...a),
    error: (...a) => console.error('[Images]', ...a),
  };

  logger.info('Starting image loader...');

  // Enable verbose logging via URL or localStorage
  try {
    const qs = new URLSearchParams(location.search);
    if (qs.has('debug') || qs.get('debugImages') === '1') {
      window.Log?.setEnabled?.(true);
      window.Log?.setLevel?.('debug');
      logger.info('Debug mode enabled for images');
    }
  } catch {
    // Ignore any errors
  }

  // --- Utilities ---
  // Extract Drive ID from various formats
  const extractDriveId = (val) => {
    if (!val) return '';
    const s = String(val);
    const m = s.match(/\/d\/([a-zA-Z0-9_-]{10,})/) || s.match(/[?&]id=([a-zA-Z0-9_-]{10,})/);
    return (m && m[1]) || s;
  };

  // Convert to Drive direct view URL (for documents only now)
  const toDrive = (idOrUrl) => {
    const id = extractDriveId(idOrUrl);
    if (!id) return '';
    const url = `https://drive.google.com/uc?export=view&id=${encodeURIComponent(id)}`;
    logger.debug('Drive ID converted:', { input: idOrUrl, id, url });
    return url;
  };

  // Removed toDriveThumb - no longer needed with local images

  const loadJson = async (url) => {
    try {
      logger.debug(`Fetching config: ${url}`);
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) {
        logger.warn(`Failed to load ${url}: ${r.status} ${r.statusText}`);
        return null;
      }
      const data = await r.json();
      logger.debug(`Loaded config from ${url}`, data);
      return data;
    } catch (error) {
      logger.error(`Error loading ${url}:`, error);
      return null;
    }
  };
  const deepMerge = (base, over) => {
    if (!over) return base || {};
    const out = JSON.parse(JSON.stringify(base || {}));
    for (const k of Object.keys(over)) {
      out[k] =
        over[k] && typeof over[k] === 'object' && !Array.isArray(over[k])
          ? deepMerge(out[k], over[k])
          : over[k];
    }
    return out;
  };
  // Convert plain rgba to gradient for CSS background-image
  const toOverlay = (s) =>
    s ? (/gradient\(/.test(s) ? s : `linear-gradient(${s}, ${s})`) : 'none';

  // Accepts either {srcId,imageId,src,image} or a direct string URL
  const pickUrl = (conf, placeholder) => {
    if (!conf) return placeholder || '';
    if (typeof conf === 'string') return conf;

    // Size hints are no longer needed with local images
    // Keeping for backward compatibility logging only
    const rawSize = conf.driveSize ?? conf.pixelSize ?? 0;
    const sizeNum = Number(rawSize) || 0;

    if (sizeNum) {
      logger.debug('Size hint (ignored for local files)', {
        size: sizeNum,
        for: conf.alt || conf.caption || 'image',
      });
    }

    // Prefer IDs if present (for backward compatibility with Drive)
    if (conf.srcId) return toDrive(conf.srcId);
    if (conf.imageId) return toDrive(conf.imageId);

    // If src/image is a Drive link, convert it; else use as-is
    if (conf.src) return /drive\.google\.com/.test(conf.src) ? toDrive(conf.src) : conf.src;
    if (conf.image) return /drive\.google\.com/.test(conf.image) ? toDrive(conf.image) : conf.image;

    return placeholder || '';
  };
  const setImg = (el, conf, placeholder) => {
    if (!el || !conf) {
      logger.debug('setImg skipped:', { hasEl: !!el, hasConf: !!conf });
      return;
    }
    const url = pickUrl(conf, placeholder);
    if (!url) {
      logger.warn('No URL for image:', { el: el?.id, conf });
      return;
    }

    // Add load/error handlers before setting src
    el.onload = () =>
      logger.info('IMG load SUCCESS', {
        element: `#${el.id || el.className || el.tagName}`,
        src: el.currentSrc || el.src,
        dimensions: `${el.naturalWidth}x${el.naturalHeight}`,
      });

    // Error handler - Drive URLs should work if permissions are correct
    el.onerror = () => {
      logger.error('IMG load FAILED', {
        element: `#${el.id || el.className || el.tagName}`,
        src: el.src,
        err: 'Image failed to load - check file path',
      });
    };

    el.src = url;
    if (conf.alt) el.alt = conf.alt;
    if (conf.width) el.width = conf.width;
    if (conf.height) el.height = conf.height;
    el.loading = conf.loading || 'lazy';
    el.decoding = conf.decoding || 'async';
    if (conf.display) el.hidden = false; // requires element to start with [hidden] in markup
    logger.debug('Image src set:', { element: el?.id || el?.className, url });
  };
  const applyBg = (el, conf, fallback) => {
    if (!el || !conf || conf.enabled === false) {
      logger.warn('applyBg skipped:', { hasEl: !!el, hasConf: !!conf, enabled: conf?.enabled });
      return;
    }
    const url = pickUrl(conf, fallback);
    if (!url) {
      logger.warn('No URL for background');
      return;
    }
    logger.info('Applying background:', { url, overlay: conf.overlay });
    el.style.setProperty('--hero-image', `url("${url}")`);
    el.style.setProperty('--hero-overlay', toOverlay(conf.overlay));
    el.style.setProperty('--hero-position', conf.position || 'center center');
    el.style.setProperty('--hero-size', conf.size || 'cover');
    el.style.setProperty('--hero-attachment', conf.attachment || 'scroll');
  };

  // --- Load configs: global + per-site (optional) ---
  const globalCfg = await loadJson('config/images.json'); // your new file
  // If your app has a site slug, set window.__SITE_SLUG (e.g., "lancaster-12")
  const siteSlug = window.__SITE_SLUG || (window.currentSite && window.currentSite.slug) || null;
  const siteCfg = siteSlug ? await loadJson(`sites/${siteSlug}/images.json`) : null;
  const cfg = deepMerge(globalCfg, siteCfg);

  logger.info('Config loading:', {
    siteSlug,
    globalCfgLoaded: !!globalCfg,
    siteCfgLoaded: !!siteCfg,
  });

  if (!cfg) {
    logger.error('No configuration loaded - check that config/images.json exists');
    return;
  }

  logger.info('Configuration status:', {
    ownerPhoto: cfg.owner?.photo?.display ? 'ON' : 'OFF',
    headerLogo: cfg.logos?.header?.display ? 'ON' : 'OFF',
    footerLogo: cfg.logos?.footer?.display ? 'ON' : 'OFF',
    heroBg: cfg.backgrounds?.hero?.enabled ? 'ON' : 'OFF',
  });

  // --- Owner ---
  if (cfg.owner?.photo?.display) {
    const ownerSection = document.getElementById('owner');
    const ownerPhoto = document.getElementById('ownerPhoto');
    const ownerCaption = document.getElementById('ownerCaption');

    logger.debug('Owner section:', {
      sectionFound: !!ownerSection,
      photoFound: !!ownerPhoto,
      srcId: cfg.owner.photo.srcId,
    });

    if (!ownerSection) logger.warn('Owner section #owner not found in DOM');
    if (!ownerPhoto) logger.warn('Owner photo #ownerPhoto not found in DOM');

    ownerSection?.removeAttribute('hidden');
    setImg(ownerPhoto, cfg.owner.photo, cfg.placeholders?.owner);
    if (ownerCaption && cfg.owner.photo.caption) ownerCaption.textContent = cfg.owner.photo.caption;
  } else {
    logger.info('Owner photo disabled in config');
  }

  // --- Logos ---
  if (cfg.logos?.header?.display) {
    const el = document.getElementById('logoHeader');
    const lightUrl = pickUrl(cfg.logos.header, cfg.placeholders?.logo);

    logger.debug('Header logo:', {
      elementFound: !!el,
      srcId: cfg.logos.header.srcId,
      url: lightUrl,
    });

    if (!el) logger.warn('Header logo element #logoHeader not found in DOM');

    setImg(el, { src: lightUrl, ...cfg.logos.header }, cfg.placeholders?.logo);
    el?.removeAttribute('hidden');

    // Dark variant (optional)
    const darkUrl = pickUrl(
      { src: cfg.logos.header.darkSrc, srcId: cfg.logos.header.darkSrcId },
      null
    );
    if (darkUrl) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const apply = () => {
        if (el) el.src = mq.matches ? darkUrl : lightUrl;
      };
      mq.addEventListener('change', apply);
      apply();
    }
  }
  if (cfg.logos?.footer?.display) {
    const el = document.getElementById('logoFooter');

    logger.debug('Footer logo:', {
      elementFound: !!el,
      srcId: cfg.logos.footer.srcId,
    });

    if (!el) logger.warn('Footer logo element #logoFooter not found in DOM');

    setImg(el, cfg.logos.footer, cfg.placeholders?.logo);
    el?.removeAttribute('hidden');
  } else {
    logger.info('Footer logo disabled in config');
  }

  // --- Hero background ---
  if (cfg.backgrounds?.hero) {
    const header = document.querySelector('header[data-bg="hero"]');
    const heroUrl = pickUrl(cfg.backgrounds.hero, cfg.placeholders?.background);

    logger.debug('Hero background check:', {
      headerFound: !!header,
      enabled: cfg.backgrounds.hero.enabled,
      imageId: cfg.backgrounds.hero.imageId,
      url: heroUrl,
    });

    if (!header) logger.warn('Header element with data-bg="hero" not found');

    // Probe the hero image to verify it loads
    if (heroUrl && cfg.backgrounds.hero.enabled) {
      const probe = new Image();
      probe.onload = () =>
        logger.info('HERO probe SUCCESS', {
          url: heroUrl,
          dimensions: `${probe.naturalWidth}x${probe.naturalHeight}`,
        });
      probe.onerror = () =>
        logger.error('HERO probe FAILED', {
          url: heroUrl,
          message: 'Check file path',
        });
      probe.src = heroUrl;
    }

    // Then apply background (next frame gives preload a head start)
    requestAnimationFrame(() => {
      applyBg(header, cfg.backgrounds.hero, cfg.placeholders?.background);
      if (header) {
        const cs = getComputedStyle(header);
        const bgImage = cs.getPropertyValue('background-image');
        logger.info('Hero CSS applied:', {
          '--hero-image': cs.getPropertyValue('--hero-image')?.substring(0, 100) + '...',
          '--hero-overlay': cs.getPropertyValue('--hero-overlay')?.substring(0, 50),
          'computed-background': bgImage?.substring(0, 150) + '...',
        });
      }
    });
  } else {
    logger.info('Hero background not configured');
  }

  // --- Optional: section backgrounds (plans/documents) ---
  const sec = cfg.backgrounds?.sections || {};
  if (sec.plans?.enabled) {
    const el = document.getElementById('plans');
    if (el)
      el.style.backgroundImage = `${sec.plans.overlay ? toOverlay(sec.plans.overlay) + ',' : ''} url("${pickUrl(sec.plans, cfg.placeholders?.background)}")`;
  }
  if (sec.documents?.enabled) {
    const el = document.getElementById('documents');
    if (el)
      el.style.backgroundImage = `${sec.documents.overlay ? toOverlay(sec.documents.overlay) + ',' : ''} url("${pickUrl(sec.documents, cfg.placeholders?.background)}")`;
  }

  // --- Lot photos ---
  const lotsCfg = cfg.lots || {};
  const fallbackLot = pickUrl(
    { src: lotsCfg.defaultImage, srcId: lotsCfg.defaultImageId },
    cfg.placeholders?.lot
  );

  // Function to hydrate a single lot card
  const hydrateLotCard = (card) => {
    const id = card.getAttribute('data-lot-id'); // e.g., "lot7"
    const raw = lotsCfg.images?.[id];
    const url = pickUrl(typeof raw === 'string' ? { src: raw } : raw, fallbackLot);
    const imgEl = card.querySelector('img.lot-thumb');
    if (imgEl) {
      imgEl.src = url;
      imgEl.alt = imgEl.alt || `Photo of ${id}`;
      imgEl.loading = 'lazy';
      imgEl.decoding = 'async';
    } else {
      const thumb = card.querySelector('.lot-thumb') || card;
      thumb.classList.add('has-image');
      thumb.style.backgroundImage = `url("${url}")`;
    }
  };

  // Initial pass for existing cards
  document.querySelectorAll('[data-lot-id]').forEach(hydrateLotCard);

  // Watch for dynamically added lot cards
  new MutationObserver((muts) => {
    for (const m of muts)
      for (const n of m.addedNodes) {
        if (!(n instanceof Element)) continue;
        if (n.matches?.('[data-lot-id]')) hydrateLotCard(n);
        n.querySelectorAll?.('[data-lot-id]').forEach(hydrateLotCard);
      }
  }).observe(document.body, { childList: true, subtree: true });

  // Listen for custom event from renderer
  window.addEventListener('lots:rendered', () =>
    document.querySelectorAll('[data-lot-id]').forEach(hydrateLotCard)
  );

  // Best-effort update for social card hero (crawlers generally read server meta only)
  const og = document.querySelector('meta[property="og:image"]');
  if (og && cfg.backgrounds?.hero) og.setAttribute('content', pickUrl(cfg.backgrounds.hero));

  // Expose debug info for troubleshooting
  window.ImagesDebug = {
    config: cfg,
    elements: {
      header: document.querySelector('header[data-bg="hero"]'),
      logoHeader: document.getElementById('logoHeader'),
      logoFooter: document.getElementById('logoFooter'),
      owner: document.getElementById('owner'),
      ownerPhoto: document.getElementById('ownerPhoto'),
    },
    test: {
      toDrive,
      pickUrl,
    },
  };

  logger.info('Image loader complete. Debug info available at window.ImagesDebug');
})();
