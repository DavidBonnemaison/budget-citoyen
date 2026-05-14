// webapp/src/components/ImpactDisplay.tsx
//
// Three household profile impact pills with footnote (D-04, D-06).
// Decision: profiles: modeste (~14k), médian (~26k), aisé (~60k) per D-06.

import type { ScenarioResult } from '../engine/types';
import { ImpactPill } from './ImpactPill';

interface ImpactDisplayProps {
  results: (ScenarioResult | null)[];
}

const PROFILE_LABELS = ['Foyer modeste', 'Foyer médian', 'Foyer aisé'] as const;
const PROFILE_INCOMES = ['~14\u00a0000\u00a0€', '~26\u00a0000\u00a0€', '~60\u00a0000\u00a0€'] as const;

export function ImpactDisplay({ results }: ImpactDisplayProps) {
  return (
    <section aria-label="Impact sur votre foyer" className="mb-8">
      <h2 className="text-xl font-semibold mb-4 text-primary">
        Impact sur votre foyer
      </h2>
      <div className="flex flex-row gap-4 overflow-x-auto pb-2">
        {PROFILE_LABELS.map((label, i) => {
          const result = results[i] ?? null;
          const impact = result
            ? result.revenuDisponible
            : null;
          return (
            <ImpactPill
              key={i}
              label={label}
              income={PROFILE_INCOMES[i]}
              impact={impact}
            />
          );
        })}
      </div>
      <p className="text-sm text-text-secondary mt-4">
        Basé sur les scénarios les plus proches.
      </p>
    </section>
  );
}
