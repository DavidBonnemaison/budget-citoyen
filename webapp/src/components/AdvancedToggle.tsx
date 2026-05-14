// webapp/src/components/AdvancedToggle.tsx
//
// Mode avancé toggle for exposing individual sub-parameter sliders (D-11).
// Decision: aria-pressed for toggle semantics — screen readers announce state.

interface AdvancedToggleProps {
  advancedMode: boolean;
  onToggle: () => void;
}

export function AdvancedToggle({ advancedMode, onToggle }: AdvancedToggleProps) {
  return (
    <button
      onClick={onToggle}
      aria-pressed={advancedMode}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-secondary transition-colors focus:outline-2 focus:outline-offset-2 focus:outline-primary"
    >
      <span>Mode avancé</span>
      <span
        className={`text-xs font-medium px-1.5 py-0.5 rounded ${advancedMode ? 'bg-primary text-text-on-accent' : 'bg-gray-200 text-text-secondary'}`}
      >
        {advancedMode ? 'Actif' : 'Inactif'}
      </span>
    </button>
  );
}
