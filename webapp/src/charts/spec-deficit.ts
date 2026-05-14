// webapp/src/charts/spec-deficit.ts
//
// Vega-Lite spec for Déficit public trajectory (D-16, D-18, D-19).
// Decision: line+area chart with diagonal line pattern fill, deuteranopia-safe #0072B2 stroke.

import type { TopLevelSpec } from 'vega-lite';
import { sharedConfig } from './config';

export const deficitSpec: TopLevelSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: 'Projection du déficit public sur 5 ans en pourcentage du PIB',
  width: 'container',
  height: 250,
  data: { values: [] },
  mark: {
    type: 'area',
    fill: 'url(#pattern-deficit)',
    stroke: '#0072B2',
    strokeWidth: 2,
    opacity: 0.7,
  },
  encoding: {
    x: { field: 'year', type: 'ordinal', title: 'Année' },
    y: { field: 'deficit', type: 'quantitative', title: '% du PIB' },
    tooltip: [
      { field: 'year', title: 'Année' },
      { field: 'deficit', title: 'Déficit (% PIB)', format: '.1f' },
    ],
  },
  config: sharedConfig,
};
