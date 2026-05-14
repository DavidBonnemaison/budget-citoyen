// webapp/src/components/ChartCell.tsx
//
// Single Vega-Lite chart with ARIA + HTML table fallback (A11Y-01, A11Y-02, D-21).
// Decision: vega-embed SVG renderer, pattern injection via global defs, sr-only table.

import { useRef, useEffect, useId } from 'react';
import vegaEmbed from 'vega-embed';
import type { TopLevelSpec } from 'vega-lite';
import { ChartTableFallback } from './ChartTableFallback';

interface ChartCellProps {
  data: Array<Record<string, unknown>>;
  spec: TopLevelSpec;
  title: string;
  isOutOfBounds?: boolean;
  warningMessage?: string | null;
}

export function ChartCell({
  data,
  spec,
  title,
  isOutOfBounds = false,
  warningMessage = null,
}: ChartCellProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const uniqueId = useId();

  useEffect(() => {
    if (!containerRef.current) return;

    const specWithData: TopLevelSpec = {
      ...spec,
      data: { values: data },
      description: `${title} — projection sur 5 ans`,
    };

    let cancelled = false;

    vegaEmbed(containerRef.current, specWithData, {
      actions: false,
      renderer: 'svg',
    }).then(({ view }) => {
      if (cancelled) {
        view.finalize();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [data, spec, title]);

  const isEmpty = data.length === 0;

  return (
    <figure className="relative">
      <figcaption id={uniqueId} className="text-sm font-semibold text-primary mb-2">
        {title}
      </figcaption>
      <div className="relative bg-white rounded-lg border border-gray-200 p-2">
        <div
          ref={containerRef}
          role="img"
          aria-labelledby={uniqueId}
          className={isOutOfBounds ? 'opacity-30' : ''}
        />
        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-text-secondary">
              Sélectionnez un scénario pour voir les projections.
            </p>
          </div>
        )}
        {!isEmpty && isOutOfBounds && (
          <div className="absolute inset-0 bg-gray-200/80 flex items-center justify-center rounded-lg">
            <p className="text-sm text-text-secondary font-medium">
              Paramètres hors domaine de validité
            </p>
          </div>
        )}
      </div>
      {warningMessage && (
        <p className="text-xs text-amber-700 mt-1" role="alert">
          {warningMessage}
        </p>
      )}
      <ChartTableFallback title={title} data={data} />
    </figure>
  );
}
