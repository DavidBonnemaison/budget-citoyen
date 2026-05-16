// webapp/vitest.config.ts
//
// Vitest 4 configuration — merges with Vite config for plugin consistency.
// Decision: jsdom environment for DOM-based component testing; css: true so Tailwind classes resolve.
// Pattern: mergeConfig pattern ensures test env inherits Vite's React + Tailwind plugins.

import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{ts,tsx}'],
      globals: false,
      css: true,
    },
  }),
);
