// webapp/src/components/ScenarioGrid.tsx
//
// Responsive scenario selection grid (D-01, D-07, D-28).
// Decision: primary flow is scenario selection first, sliders second.
// Grid layout: 1-col mobile → 2-col tablet → 3-col desktop (UI-SPEC responsive contract).

import type { ScenarioDefinition } from '../engine/types';
import { ScenarioCard } from './ScenarioCard';

interface ScenarioGridProps {
  scenarios: ScenarioDefinition[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ScenarioGrid({ scenarios, selectedId, onSelect }: ScenarioGridProps) {
  return (
    <section aria-label="Scénarios disponibles">
      <h2 className="text-lg font-semibold mb-4 text-primary">
        Choisissez un scénario pour commencer
      </h2>
      {scenarios.length === 0 ? (
        <p className="text-sm text-text-disabled">
          Chargement des scénarios…
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {scenarios.map((scenario) => (
            <ScenarioCard
              key={scenario.id}
              scenario={scenario}
              isSelected={scenario.id === selectedId}
              onSelect={() => onSelect(scenario.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
