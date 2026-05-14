// webapp/src/components/ChartGrid.tsx
//
// Responsive 2×2 Vega-Lite chart grid (D-17, D-19).
// Decision: renders hidden SVG defs element for pattern fills, maps 4 specs to ChartCells.

import type { MacroResult } from '../engine/types';
import type { TopLevelSpec } from 'vega-lite';
import { ChartCell } from './ChartCell';
import { CHART_PATTERNS_SVG } from '../charts/patterns';
import { deficitSpec } from '../charts/spec-deficit';
import { debtSpec } from '../charts/spec-debt';
import { gdpSpec } from '../charts/spec-gdp';
import { employmentSpec } from '../charts/spec-employment';

interface ChartGridProps {
  macroResult: MacroResult | null;
}

interface ChartConfig {
  spec: TopLevelSpec;
  title: string;
  field: string;
}

const CHART_CONFIGS: ChartConfig[] = [
  { spec: deficitSpec, title: 'Déficit (% PIB)', field: 'deficit' },
  { spec: debtSpec, title: 'Dette (% PIB)', field: 'debt' },
  { spec: gdpSpec, title: 'Croissance PIB (%)', field: 'gdp_growth' },
  { spec: employmentSpec, title: 'Emploi (milliers)', field: 'employment' },
];

export function ChartGrid({ macroResult }: ChartGridProps) {
  const isOutOfBounds = macroResult?.isOutOfBounds ?? false;
  const warningMessage = macroResult?.warningMessage ?? null;

  const chartData: Array<Record<string, unknown>> = macroResult
    ? Array.from({ length: macroResult.deficitTrajectory.length }, (_, i) => ({
        year: i + 1,
        deficit: macroResult.deficitTrajectory[i],
        debt: macroResult.debtTrajectory[i],
        gdp_growth: macroResult.gdpGrowthTrajectory[i],
        employment: macroResult.employmentTrajectory[i],
      }))
    : [];

  return (
    <section aria-label="Projections macroéconomiques">
      <h2 className="text-xl font-semibold mb-4 text-primary">
        Projections macroéconomiques
      </h2>

      {/* Hidden SVG defs for pattern fills (D-19, Pitfall 2 mitigation) */}
      <svg
        aria-hidden="true"
        className="absolute w-0 h-0 overflow-hidden"
        dangerouslySetInnerHTML={{ __html: CHART_PATTERNS_SVG }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {CHART_CONFIGS.map((config) => (
          <ChartCell
            key={config.field}
            data={chartData}
            spec={config.spec}
            title={config.title}
            isOutOfBounds={isOutOfBounds}
            warningMessage={warningMessage}
          />
        ))}
      </div>
    </section>
  );
}
