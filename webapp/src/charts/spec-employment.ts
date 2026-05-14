// webapp/src/charts/spec-employment.ts
//
// Vega-Lite spec for Emploi trajectory (D-16, D-18, D-19).
// Decision: line+area chart with vertical stripe pattern fill, deuteranopia-safe #CC79A7 stroke.

import type { TopLevelSpec } from 'vega-lite';
import { sharedConfig } from './config';

export const employmentSpec: TopLevelSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: "Projection de l'emploi sur 5 ans en milliers",
  width: 'container',
  height: 250,
  data: { values: [] },
  mark: {
    type: 'area',
    fill: 'url(#pattern-employment)',
    stroke: '#CC79A7',
    strokeWidth: 2,
    opacity: 0.7,
  },
  encoding: {
    x: { field: 'year', type: 'ordinal', title: 'Année' },
    y: { field: 'employment', type: 'quantitative', title: 'Milliers' },
    tooltip: [
      { field: 'year', title: 'Année' },
      { field: 'employment', title: 'Emploi (milliers)', format: '.1f' },
    ],
  },
  config: sharedConfig,
};
