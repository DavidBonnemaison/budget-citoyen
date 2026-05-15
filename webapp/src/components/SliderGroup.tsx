// webapp/src/components/SliderGroup.tsx
//
// Slider sections with réinitialiser button (D-09, D-14).
// Decision: all 5 levers always visible — only 5 sliders, no collapsing needed.

import { LeverSlider } from './LeverSlider';
import { LEVER_MAPPINGS } from '../state/index-map';

interface SliderGroupProps {
  disabled: boolean;
  sliderValues: Record<string, number>;
  advancedValues: Record<string, number[]>;
  onValueChange: (key: string, value: number) => void;
  onSubSliderChange: (key: string, subIdx: number, value: number) => void;
  onDragEnd: (key: string, value: number) => void;
  onReset: () => void;
  advancedMode: boolean;
}

const LEVER_ORDER = ['ir', 'is', 'tva', 'cotisations', 'depenses'];

export function SliderGroup({
  disabled,
  sliderValues,
  advancedValues,
  onValueChange,
  onSubSliderChange,
  onDragEnd,
  onReset,
  advancedMode,
}: SliderGroupProps) {
  return (
    <section aria-label="Curseurs budgétaires" className="space-y-2">
      {LEVER_ORDER.map((key) => {
        const mapping = LEVER_MAPPINGS[key];
        if (!mapping) return null;

        return (
          <div
            key={key}
            className="bg-secondary rounded-lg p-4"
          >
            <div className="text-lg font-semibold text-primary flex items-center justify-between mb-2">
              <span>{mapping.name}</span>
              <span className="text-sm text-text-secondary ml-2 shrink-0">
                {(() => {
                  const val = advancedMode && advancedValues[key]
                    ? advancedValues[key].reduce((s, v, i) => s + v * (LEVER_MAPPINGS[key]?.weights?.[i] ?? 0), 0)
                    : sliderValues[key] ?? 0;
                  return val !== 0 ? `${val > 0 ? '+' : ''}${Math.round(val)} %` : '0 %';
                })()}
              </span>
            </div>
            <div className="space-y-4">
              {/* Main lever slider — read-only weighted average in advanced mode */}
              <LeverSlider
                label={`Variation (${mapping.name})`}
                minValue={-15}
                maxValue={15}
                step={1}
                value={(() => {
                  if (advancedMode && advancedValues[key]) {
                    const subs = advancedValues[key];
                    let ws = 0;
                    for (let i = 0; i < subs.length; i++) {
                      ws += subs[i] * (mapping.weights[i] ?? 0);
                    }
                    return Math.round(ws);
                  }
                  return sliderValues[key];
                })()}
                onValueChange={(v) => onValueChange(key, v)}
                onDragEnd={(v) => onDragEnd(key, v)}
                disabled={disabled || advancedMode}
              />

              {/* Advanced sub-parameter sliders */}
              {advancedMode &&
                mapping.subParams.map((subParam, subIdx) => (
                  <LeverSlider
                    key={subParam}
                    label={subParam}
                    minValue={-15}
                    maxValue={15}
                    step={1}
                    value={
                      advancedValues[key]?.[subIdx] ?? sliderValues[key]
                    }
                    onValueChange={(v) => onSubSliderChange(key, subIdx, v)}
                    onDragEnd={(v) => onDragEnd(key, v)}
                    disabled={disabled}
                  />
                ))}
            </div>
          </div>
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
