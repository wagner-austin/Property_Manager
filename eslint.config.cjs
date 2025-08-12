// eslint.config.cjs
const js = require('@eslint/js');
const globals = require('globals');

/** @type {import('eslint').Linter.FlatConfig[]} */
module.exports = [
  // Replace old .eslintignore (you can delete that file)
  { ignores: ['node_modules/**', 'dist/**', 'build/**', 'deployment.zip'] },

  // Core recommended rules
  js.configs.recommended,

  {
    files: ['js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'script', // your code isn't ESM; if it becomes ESM, switch to 'module'
      globals: {
        ...globals.browser, // window, document, fetch, etc.
      },
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // keep no-undef to catch typos; already in recommended but explicit is fine
      'no-undef': 'error',
    },
  },
];