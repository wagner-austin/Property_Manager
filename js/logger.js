(function (global) {
  'use strict';

  const hasConsole = typeof global.console !== 'undefined';
  const c = hasConsole ? global.console : null;

  const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
  let level = 'info';
  let enabled = true;

  function setEnabled(v) {
    enabled = !!v;
  }
  function setLevel(l) {
    if (Object.prototype.hasOwnProperty.call(LEVELS, l)) level = l;
  }
  function ok(l) {
    return enabled && LEVELS[l] >= LEVELS[level];
  }

  const Log = {
    get enabled() {
      return enabled;
    },
    setEnabled,
    setLevel,

    // Core logging methods
    debug(...args) {
      if (ok('debug') && c && c.debug) c.debug(...args);
    },
    info(...args) {
      if (ok('info') && c && c.info) c.info(...args);
    },
    warn(...args) {
      if (ok('warn') && c && c.warn) c.warn(...args);
    },
    error(...args) {
      if (c && c.error) c.error(...args);
    },

    // Compatibility methods for app-multisite.js
    log(...args) {
      if (ok('info') && c && c.log) c.log(...args);
    },
    event(name, data) {
      if (ok('debug') && c && c.log) c.log(`[event] ${name}`, data);
    },
    time(label) {
      if (ok('debug') && c && c.time) c.time(label);
    },
    timeEnd(label) {
      if (ok('debug') && c && c.timeEnd) c.timeEnd(label);
    },

    // Grouping methods
    group(...args) {
      if (c && c.group) c.group(...args);
    },
    groupEnd() {
      if (c && c.groupEnd) c.groupEnd();
    },

    // Helper method
    withPrefix(prefix) {
      return {
        debug: (...a) => Log.debug(prefix, ...a),
        info: (...a) => Log.info(prefix, ...a),
        warn: (...a) => Log.warn(prefix, ...a),
        error: (...a) => Log.error(prefix, ...a),
      };
    },
  };

  try {
    const qs = global.location ? global.location.search : '';
    const params = new URLSearchParams(qs);
    if (params.has('log')) enabled = params.get('log') !== '0';
    if (params.has('debug')) enabled = true;
    const ls = global.localStorage;
    if (ls && ls.getItem('log') === '1') enabled = true;
    if (ls && ls.getItem('debugLogs') === '1') enabled = true;
  } catch {
    // Ignore URL/storage errors gracefully
  }

  global.Log = Log;
})(typeof window !== 'undefined' ? window : globalThis);
