// webapp/src/charts/spec-gdp.ts
//
// Vega-Lite spec for Croissance du PIB trajectory (D-16, D-18, D-19).
// Decision: line+area chart with crosshatch pattern fill, deuteranopia-safe #009E73 stroke.

import type { TopLevelSpec } from 'vega-lite';
import { sharedConfig } from './config';

export const gdpSpec: TopLevelSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: 'Projection de la croissance du PIB sur 5 ans en pourcentage annuel',
  width: 'container',
  height: 250,
  data: { values: [] },
  mark: {
    type: 'area',
    fill: 'url(#pattern-gdp)',
    stroke: '#009E73',
    strokeWidth: 2,
    opacity: 0.7,
  },
  encoding: {
    x: { field: 'year', type: 'ordinal', title: 'Année' },
    y: { field: 'gdp_growth', type: 'quantitative', title: '% annuel' },
    tooltip: [
      { field: 'year', title: 'Année' },
      { field: 'gdp_growth', title: 'Croissance PIB (%)', format: '.1f' },
    ],
  },
  config: sharedConfig,
};
