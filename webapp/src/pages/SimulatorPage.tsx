// webapp/src/pages/SimulatorPage.tsx
//
// Split-panel simulator layout: left (380px, scenarios+sliders) + right (flex, impact+charts) (D-22).
// Decision: mobile accordion for left panel (D-24), scroll reset on scenario change.

import { useEffect, useRef, useMemo } from 'react';
import { ScenarioGrid } from '../components/ScenarioGrid';
import { SliderGroup } from '../components/SliderGroup';
import { AdvancedToggle } from '../components/AdvancedToggle';
import { ImpactDisplay } from '../components/ImpactDisplay';
import { ChartGrid } from '../components/ChartGrid';
import { Footer } from '../components/Footer';
import type { SimulationState } from '../hooks/useSimulation';

interface SimulatorPageProps {
  simulation: SimulationState;
}

export function SimulatorPage({ simulation }: SimulatorPageProps) {
  const rightPanelRef = useRef<HTMLDivElement>(null);

  // Scroll reset on scenario change
  useEffect(() => {
    if (rightPanelRef.current && simulation.selectedScenarioId) {
      rightPanelRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [simulation.selectedScenarioId]);

  const isPreselect = simulation.phase === 'preselect';

  const sliderValues = useMemo<Record<string, number>>(
    () => ({
      ir: simulation.sliderState.ir,
      is: simulation.sliderState.is,
      tva: simulation.sliderState.tva,
      cotisations: simulation.sliderState.cotisations,
      depenses: simulation.sliderState.depenses,
    }),
    [
      simulation.sliderState.ir,
      simulation.sliderState.is,
      simulation.sliderState.tva,
      simulation.sliderState.cotisations,
      simulation.sliderState.depenses,
    ],
  );

  return (
    <div className="flex flex-col lg:flex-row min-h-screen">
      {/* Left panel — Desktop: fixed 380px | Mobile: accordion */}
      <details className="lg:hidden bg-secondary border-b border-gray-200" open>
        <summary className="p-4 text-lg font-semibold text-primary cursor-pointer list-none">
          Réglages
        </summary>
        <div className="px-4 pb-4 space-y-4">
          <ScenarioGrid
            scenarios={simulation.scenarios}
            selectedId={simulation.selectedScenarioId}
            onSelect={simulation.selectScenario}
          />
          {!isPreselect && (
            <>
              <AdvancedToggle
                advancedMode={simulation.advancedMode}
                onToggle={simulation.toggleAdvanced}
              />
              <SliderGroup
                disabled={isPreselect}
                sliderValues={sliderValues}
                advancedValues={simulation.advancedValues}
                onValueChange={simulation.handleSliderChange}
                onSubSliderChange={simulation.handleSubSliderChange}
                onDragEnd={simulation.handleDragEnd}
                onReset={simulation.handleReset}
                advancedMode={simulation.advancedMode}
              />
            </>
          )}
        </div>
      </details>

      {/* Left panel — Desktop */}
      <aside className="hidden lg:block lg:w-[380px] lg:shrink-0 p-6 bg-secondary border-r border-gray-200 overflow-y-auto lg:max-h-screen">
        <ScenarioGrid
          scenarios={simulation.scenarios}
          selectedId={simulation.selectedScenarioId}
          onSelect={simulation.selectScenario}
        />
        {!isPreselect && (
          <>
            <div className="mt-6">
              <AdvancedToggle
                advancedMode={simulation.advancedMode}
                onToggle={simulation.toggleAdvanced}
              />
            </div>
            <div className="mt-4">
              <SliderGroup
                disabled={isPreselect}
                sliderValues={sliderValues}
                advancedValues={simulation.advancedValues}
                onValueChange={simulation.handleSliderChange}
                onSubSliderChange={simulation.handleSubSliderChange}
                onDragEnd={simulation.handleDragEnd}
                onReset={simulation.handleReset}
                advancedMode={simulation.advancedMode}
              />
            </div>
          </>
        )}
      </aside>

      {/* Right panel */}
      <main
        ref={rightPanelRef}
        className="flex-1 p-6 overflow-y-auto lg:max-h-screen"
      >
        <ImpactDisplay results={simulation.microResults} />
        <ChartGrid macroResult={simulation.macroResult} />
        <Footer />
      </main>
    </div>
  );
}
