// webapp/src/charts/config.ts
//
// Shared Vega-Lite configuration for all Budget Citoyen macro trajectory charts.
// Decision: D-17 (2×2 grid), D-19 (pattern fills), A11Y-01 (ARIA labels),
//   A11Y-03 (deuteranopia-safe colors). Single source of truth for chart theming.

import type { Config } from 'vega-lite';

export const sharedConfig: Config = {
  aria: true,
  background: 'transparent',
  font: 'Inter, system-ui, sans-serif',

  axis: {
    labelFontSize: 12,
    titleFontSize: 13,
    gridColor: '#E5E7EB',
    domainColor: '#9CA3AF',
  },

  view: {
    stroke: 'transparent',
  },

  legend: {
    orient: 'bottom',
    labelFontSize: 12,
  },

  range: {
    category: ['#0072B2', '#E69F00', '#009E73', '#CC79A7'],
  },
};
