// webapp/src/components/ScenarioCard.tsx
//
// Individual scenario selection card with hover, selected, and keyboard states.
// Decision: <button> element for native keyboard support (Tab, Enter/Space to select).
// Selected state: ring-2 accent per UI-SPEC Interactive Component Contract.

import type { ScenarioDefinition } from '../engine/types';

interface ScenarioCardProps {
  scenario: ScenarioDefinition;
  isSelected: boolean;
  onSelect: () => void;
}

export function ScenarioCard({ scenario, isSelected, onSelect }: ScenarioCardProps) {
  return (
    <button
      onClick={onSelect}
      aria-pressed={isSelected}
      aria-label={`Sélectionner le scénario ${scenario.name}`}
      className={`
        bg-secondary rounded-lg p-4 text-left w-full min-h-[44px]
        border border-slate-200 shadow-sm overflow-hidden
        hover:scale-[1.02] hover:shadow-md transition-all duration-200
        focus:outline-2 focus:outline-offset-2 focus:outline-primary
        ${isSelected ? 'ring-2 ring-primary shadow-md border-primary' : ''}
      `}
    >
      <h3 className="text-lg font-semibold text-primary mb-1 break-words">
        {scenario.name}
      </h3>
      <p className="text-sm text-text-secondary line-clamp-3">
        {scenario.description}
      </p>
    </button>
  );
}
