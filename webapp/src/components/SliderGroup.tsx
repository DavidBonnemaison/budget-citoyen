// webapp/src/components/SliderGroup.tsx
//
// Collapsible slider sections with réinitialiser button (D-09, D-14).
// Decision: native <details> + <summary> for collapsible behavior (no JS needed).
// Default: IR ménages expanded, others collapsed.

import { LeverSlider } from './LeverSlider';
import { LEVER_MAPPINGS } from '../state/index-map';
import type { FiscalSliderProps } from './LeverSlider';

interface SliderGroupProps {
  disabled: boolean;
  sliderValues: Record<string, number>;
  onValueChange: (key: string, value: number) => void;
  onDragEnd: (key: string, value: number) => void;
  onReset: () => void;
  advancedMode: boolean;
}

const LEVER_ORDER = ['ir', 'is', 'tva', 'cotisations', 'depenses'];

export function SliderGroup({
  disabled,
  sliderValues,
  onValueChange,
  onDragEnd,
  onReset,
  advancedMode,
}: SliderGroupProps) {
  return (
    <section aria-label="Curseurs budgétaires" className="space-y-2">
      {LEVER_ORDER.map((key, index) => {
        const mapping = LEVER_MAPPINGS[key];
        if (!mapping) return null;

        const isFirst = index === 0;

        return (
          <details
            key={key}
            open={isFirst || advancedMode}
            className="bg-secondary rounded-lg p-4 group"
          >
            <summary className="text-lg font-semibold text-primary cursor-pointer list-none flex items-center justify-between">
              <span>{mapping.name}</span>
              <span className="text-sm text-text-secondary group-open:hidden ml-2 shrink-0">
                {sliderValues[key] != null && sliderValues[key] !== 0
                  ? `${sliderValues[key] > 0 ? '+' : ''}${sliderValues[key]} %`
                  : '0 %'}
              </span>
            </summary>
            <div className="mt-4 space-y-4">
              {/* Main lever slider */}
              <LeverSlider
                label={`Variation (${mapping.name})`}
                minValue={-30}
                maxValue={30}
                step={1}
                value={sliderValues[key]}
                onValueChange={(v) => onValueChange(key, v)}
                onDragEnd={(v) => onDragEnd(key, v)}
                disabled={disabled}
              />

              {/* Advanced sub-parameter sliders (D-11) */}
              {advancedMode &&
                mapping.subParams.map((subParam, subIdx) => (
                  <LeverSlider
                    key={subParam}
                    label={subParam}
                    minValue={-30}
                    maxValue={30}
                    step={1}
                    value={sliderValues[key] * mapping.weights[subIdx]}
                    onValueChange={(v) => onValueChange(key, v)}
                    onDragEnd={(v) => onDragEnd(key, v)}
                    disabled={disabled}
                  />
                ))}
            </div>
          </details>
        );
      })}

      {/* Réinitialiser button (D-14) */}
      <button
        onClick={onReset}
        disabled={disabled}
        className="w-full mt-4 px-4 py-2 border border-gray-300 rounded-lg text-sm text-text-secondary hover:bg-secondary hover:border-destructive hover:text-destructive transition-colors focus:outline-2 focus:outline-offset-2 focus:outline-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Réinitialiser
      </button>
    </section>
  );
}
