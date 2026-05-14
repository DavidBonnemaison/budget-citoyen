// webapp/vite.config.ts
//
// Vite 6 configuration with React plugin and Tailwind CSS 4.3 plugin.
// Decision: no WASM config needed — Phase 3 is pure TypeScript.

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
  },
  build: {
    target: 'es2022',
  },
});
