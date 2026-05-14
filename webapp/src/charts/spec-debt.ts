// webapp/src/charts/spec-debt.ts
//
// Vega-Lite spec for Dette publique trajectory (D-16, D-18, D-19).
// Decision: line+area chart with dot pattern fill, deuteranopia-safe #E69F00 stroke.

import type { TopLevelSpec } from 'vega-lite';
import { sharedConfig } from './config';

export const debtSpec: TopLevelSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: 'Projection de la dette publique sur 5 ans en pourcentage du PIB',
  width: 'container',
  height: 250,
  data: { values: [] },
  mark: {
    type: 'area',
    fill: 'url(#pattern-debt)',
    stroke: '#E69F00',
    strokeWidth: 2,
    opacity: 0.7,
  },
  encoding: {
    x: { field: 'year', type: 'ordinal', title: 'Année' },
    y: { field: 'debt', type: 'quantitative', title: '% du PIB' },
    tooltip: [
      { field: 'year', title: 'Année' },
      { field: 'debt', title: 'Dette (% PIB)', format: '.1f' },
    ],
  },
  config: sharedConfig,
};
