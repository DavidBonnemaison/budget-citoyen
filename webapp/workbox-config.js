// webapp/workbox-config.js
//
// Workbox build configuration for precache manifest generation.
// Run after Vite build: npx workbox-build --config workbox-config.js

module.exports = {
  globDirectory: './dist/',
  globPatterns: [
    'index.html',
    'assets/**/*.js',
    'assets/**/*.css',
    'assets/**/*.svg',
    'data/**/*.json',
    'data/**/*.bin',
  ],
  swDest: 'dist/sw.js',
  swSrc: 'sw.js',
};
