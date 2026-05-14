// webapp/src/components/LeverSlider.tsx
//
// WAI-ARIA compliant fiscal lever slider using React Aria useSlider (D-08, D-10, D-13, D-15).
// Decision: React Aria provides 14 ARIA attributes + hidden native input for touch screen readers.
// Pattern from RESEARCH.md lines 560-673: Full Slider Component with Budget Citoyen theming.

import { useRef, useMemo, useTransition } from 'react';
import { useSlider, useSliderThumb } from 'react-aria';
import { useSliderState } from 'react-stately';
import type { SliderStateOptions } from 'react-stately';

// ── Props ─────────────────────────────────────────────────────────────────────

export interface FiscalSliderProps {
  label: string;
  minValue: number;
  maxValue: number;
  step: number;
  defaultValue?: number;
  value?: number;
  onValueChange: (value: number) => void;
  onDragEnd: (value: number) => void;
  disabled?: boolean;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function LeverSlider({
  label,
  minValue,
  maxValue,
  step,
  defaultValue = 0,
  value,
  onValueChange,
  onDragEnd,
  disabled = false,
}: FiscalSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isPending, startTransition] = useTransition();

  const formatter = useMemo(
    () =>
      new Intl.NumberFormat('fr-FR', {
        style: 'percent',
        signDisplay: 'always',
        maximumFractionDigits: 0,
      }),
    [],
  );

  const sliderStateOptions: SliderStateOptions<number[]> = {
    value: value !== undefined ? [value] : undefined,
    defaultValue: [defaultValue],
    minValue,
    maxValue,
    step,
    label,
    numberFormatter: formatter,
    isDisabled: disabled,
    onChange: (vals: number[]) => onValueChange(vals[0]),
    onChangeEnd: (vals: number[]) => {
      startTransition(() => onDragEnd(vals[0]));
    },
  };

  const state = useSliderState(sliderStateOptions);
  const { groupProps, trackProps, labelProps, outputProps } = useSlider(
    sliderStateOptions,
    state,
    trackRef,
  );
  const { thumbProps, inputProps } = useSliderThumb(
    { index: 0, trackRef, inputRef },
    state,
  );

  const currentValue = state.values[0];
  const pct = ((currentValue - minValue) / (maxValue - minValue)) * 100;
  const zeroPct = ((-minValue) / (maxValue - minValue)) * 100;
  const showNotch = minValue <= 0 && maxValue >= 0;

  return (
    <div
      {...groupProps}
      role="group"
      aria-label={label}
      className={`relative w-full${disabled ? ' opacity-50 cursor-not-allowed' : ''}`}
    >
      {/* ── Label + Value ── */}
      <div className="flex justify-between items-center mb-1">
        <label {...labelProps} className="text-sm font-normal leading-snug text-text-secondary">
          {label}
        </label>
        <output
          {...outputProps}
          className="text-sm font-semibold tabular-nums text-primary"
        >
          {state.getThumbValueLabel(0)}
        </output>
      </div>

      {/* ── Track Container ── */}
      <div
        {...trackProps}
        ref={trackRef}
        className={`relative h-3 rounded-full cursor-pointer touch-none ${isPending ? 'animate-pulse' : ''} ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        style={{
          background: `linear-gradient(to right, #1E3A5F 0%, #1E3A5F ${pct}%, #CBD5E1 ${pct}%, #CBD5E1 100%)`,
        }}
      >
        {/* Baseline Notch (D-13) */}
        {showNotch && (
          <div
            aria-hidden="true"
            className="absolute top-0 bottom-0 w-0.5 bg-white/50"
            style={{ left: `${zeroPct}%`, transform: 'translateX(-50%)' }}
          />
        )}

        {/* Thumb (44×44px touch target) */}
        {!disabled && (
          <div
            {...thumbProps}
            className="absolute top-1/2 w-11 h-11 bg-primary rounded-full shadow-md cursor-grab active:cursor-grabbing focus:outline-2 focus:outline-offset-2 focus:outline-primary"
            style={{ left: `${pct}%`, transform: 'translate(-50%, -50%)' }}
          >
            {/* Hidden native input for touch screen readers */}
            <input {...inputProps} ref={inputRef} />
          </div>
        )}
      </div>

      {/* "Actuel" label at baseline (D-13) */}
      {showNotch && (
        <span
          aria-hidden="true"
          className="absolute text-xs text-slate-400 mt-1"
          style={{ left: `${zeroPct}%`, transform: 'translateX(-50%)' }}
        >
          Actuel
        </span>
      )}
    </div>
  );
}
