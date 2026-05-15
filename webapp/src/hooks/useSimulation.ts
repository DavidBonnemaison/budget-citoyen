// webapp/src/hooks/useSimulation.ts
//
// Central simulation hook: state machine (LOADING→PRESELECT→DISPLAYING→ERROR),
// WorkerOrchestrator coordination, interpolation, URL state restore (D-07, D-15, D-23).
// Decision: main-thread interpolation for MVP (OQ3 — simpler and <1ms per call).

import { useState, useRef, useCallback, useEffect, useTransition } from 'react';
import { WorkerOrchestrator } from '../workers/orchestrator';
import { ScenarioCache } from '../engine/scenario-cache';
import { interpolateScenarios } from '../state/interpolation';
import { LEVER_MAPPINGS } from '../state/index-map';
import type { SliderState, URLState, InterpolationResult } from '../state/types';
import type { ScenarioDefinition, ScenarioResult, MacroResult } from '../engine/types';

// ── Constants ─────────────────────────────────────────────────────────────────

const DEFAULT_SLIDER_STATE: SliderState = {
  ir: 0,
  is: 0,
  tva: 0,
  cotisations: 0,
  depenses: 0,
};

const PROFILE_INDICES = [0, 1, 2];

export type SimulationPhase = 'loading' | 'preselect' | 'displaying' | 'error';

export interface LoadProgress {
  phase: string;
  percent: number;
}

export interface SimulationState {
  phase: SimulationPhase;
  scenarios: ScenarioDefinition[];
  selectedScenarioId: string | null;
  sliderState: SliderState;
  advancedValues: Record<string, number[]>;
  microResults: (ScenarioResult | null)[];
  macroResult: MacroResult | null;
  isComputing: boolean;
  errorMessage: string | null;
  loadProgress: LoadProgress;
  advancedMode: boolean;
  init: () => Promise<void>;
  selectScenario: (id: string) => Promise<void>;
  handleSliderChange: (key: string, value: number) => void;
  handleSubSliderChange: (key: string, subIdx: number, value: number) => void;
  handleDragEnd: (key: string, value: number) => void;
  handleReset: () => void;
  toggleAdvanced: () => void;
  retry: () => void;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useSimulation(): SimulationState {
  const [phase, setPhase] = useState<SimulationPhase>('loading');
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [sliderState, setSliderState] = useState<SliderState>(DEFAULT_SLIDER_STATE);
  const [microResults, setMicroResults] = useState<(ScenarioResult | null)[]>([null, null, null]);
  const [macroResult, setMacroResult] = useState<MacroResult | null>(null);
  const [isComputing, setIsComputing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loadProgress, setLoadProgress] = useState<LoadProgress>({ phase: '', percent: 0 });
  const [advancedMode, setAdvancedMode] = useState(false);
  const [advancedValues, setAdvancedValues] = useState<Record<string, number[]>>({});
  const [isPending, startTransition] = useTransition();

  const orchestratorRef = useRef<WorkerOrchestrator | null>(null);
  const cacheRef = useRef<ScenarioCache | null>(null);
  const baselineResultsRef = useRef<(ScenarioResult | null)[]>([null, null, null]);

  // ── Helpers ──

  const computeDeltas = useCallback((results: (ScenarioResult | null)[]) => {
    return results.map((r, i) => {
      const baseline = baselineResultsRef.current[i];
      if (!r || !baseline) return r;
      return { ...r, revenuDisponible: r.revenuDisponible - baseline.revenuDisponible };
    });
  }, []);

  // ── Init ──

  const init = useCallback(async () => {
    setPhase('loading');
    setLoadProgress({ phase: 'Récupération des données…', percent: 10 });

    try {
      const orchestrator = new WorkerOrchestrator();
      orchestratorRef.current = orchestrator;

      // Fetch scenario data
      setLoadProgress({ phase: 'Récupération des données…', percent: 30 });
      const scenariosResponse = await fetch('/data/scenarios-v2025.1.json');
      if (!scenariosResponse.ok) throw new Error('Échec du chargement des scénarios');
      const scenariosText = await scenariosResponse.text();

      // Fetch shock matrix
      setLoadProgress({ phase: 'Récupération des données…', percent: 50 });
      const matrixResponse = await fetch('/data/shock-matrix-v2025.1.bin?t=' + Date.now());
      if (!matrixResponse.ok) throw new Error('Échec du chargement de la matrice');
      const matrixBytes = await matrixResponse.arrayBuffer();

      // Init workers
      setLoadProgress({ phase: 'Initialisation du moteur de simulation…', percent: 70 });
      await orchestrator.init(scenariosText, matrixBytes);

      // Build cache from JSON
      setLoadProgress({ phase: 'Initialisation du moteur de simulation…', percent: 90 });
      const docs = JSON.parse(scenariosText) as Array<{
        definition: ScenarioDefinition;
        results: Record<string, ScenarioResult>;
      }>;
      const cache = ScenarioCache.fromDocs(docs);
      cacheRef.current = cache;
      setScenarios(cache.listScenarios());

      // Restore from URL if present
      const params = new URLSearchParams(window.location.search);
      const encoded = params.get('state');
      if (encoded) {
        const { decodeState } = await import('../state/url-codec');
        const restored = decodeState(encoded);
        if (restored) {
          setSliderState(restored.p);
          if (restored.a) setAdvancedMode(true);
          if (restored.s) {
            setSelectedScenarioId(restored.s);
            setPhase('displaying');
            // trigger scenario select
            const scenario = cache.listScenarios().find((s) => s.id === restored.s);
            if (scenario) {
              const results = await Promise.all(
                PROFILE_INDICES.map((i) => orchestrator.simulate(restored.s!, i)),
              );
              setMicroResults(results);
              orchestrator.project(restored.p.ir / 100, restored.p.is / 100, 5).then(setMacroResult);
            }
          } else {
            setPhase('preselect');
          }
          setLoadProgress({ phase: 'Prêt', percent: 100 });
          return;
        }
      }

      setLoadProgress({ phase: 'Prêt', percent: 100 });

      // Auto-select baseline scenario (first in the list)
      const scenarios = cache.listScenarios();
      if (scenarios.length > 0) {
        try {
          const baselineId = scenarios[0].id;
          const baselineResults = await Promise.all(
            PROFILE_INDICES.map((i) => orchestrator.simulate(baselineId, i)),
          );
          baselineResultsRef.current = baselineResults;
          setSelectedScenarioId(baselineId);
          setMicroResults(computeDeltas(baselineResults));

          const def = scenarios[0];
          setSliderState({
            ir: def.parameterOverrides['ir'] ?? 0,
            is: def.parameterOverrides['is'] ?? 0,
            tva: def.parameterOverrides['tva'] ?? 0,
            cotisations: def.parameterOverrides['cotisations'] ?? 0,
            depenses: def.parameterOverrides['depenses'] ?? 0,
          });

          orchestrator.project(0, 0, 5).then((result) => {
            if (result) setMacroResult(result);
          });

          setPhase('displaying');
          return;
        } catch {
          // Fall through to preselect if baseline fails
        }
      }

      setPhase('preselect');
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Erreur inconnue');
      setPhase('error');
    }
  }, []);

  // ── Auto-init on mount ──

  useEffect(() => {
    init();
  }, [init]);

  // ── Select scenario ──

  const selectScenario = useCallback(
    async (id: string) => {
      const orchestrator = orchestratorRef.current;
      const cache = cacheRef.current;
      if (!orchestrator || !cache) return;

      setPhase('displaying');
      setSelectedScenarioId(id);

      try {
        const results = await Promise.all(
          PROFILE_INDICES.map((i) => orchestrator.simulate(id, i)),
        );

        // If this is the baseline, store raw results for delta computation
        const isBaseline = cache.listScenarios()[0]?.id === id;
        if (isBaseline) {
          baselineResultsRef.current = results;
        }

        setMicroResults(computeDeltas(results));

        const def = cache.listScenarios().find((s) => s.id === id);
        const params = def ? (def.parameterOverrides as Record<string, number>) : {};
        const newSliders: Record<string, number> = {};
        for (const [leverKey, mapping] of Object.entries(LEVER_MAPPINGS)) {
          let ws = 0;
          let totalW = 0;
          for (let i = 0; i < mapping.subParams.length; i++) {
            const subVal = params[mapping.subParams[i]];
            if (subVal !== undefined) {
              ws += subVal * mapping.weights[i];
              totalW += mapping.weights[i];
            }
          }
          newSliders[leverKey] = totalW > 0 ? Math.round(ws / totalW) : 0;
        }
        setSliderState({
          ir: newSliders['ir'] ?? 0,
          is: newSliders['is'] ?? 0,
          tva: newSliders['tva'] ?? 0,
          cotisations: newSliders['cotisations'] ?? 0,
          depenses: newSliders['depenses'] ?? 0,
        });

        orchestrator.project(
          (newSliders['ir'] ?? 0) / 100,
          (newSliders['is'] ?? 0) / 100,
          5,
        ).then((result) => {
          if (result) setMacroResult(result);
        });
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : 'Erreur de simulation');
        setPhase('error');
      }
    },
    [computeDeltas],
  );

  // ── Slider change ──

  const handleSliderChange = useCallback(
    (key: string, value: number) => {
      const newState = { ...sliderState, [key]: value };
      setSliderState(newState);

      // In advanced mode, reset sub-sliders to match main slider
      const mapping = LEVER_MAPPINGS[key];
      if (mapping) {
        setAdvancedValues((prev) => ({
          ...prev,
          [key]: mapping.subParams.map(() => value),
        }));
      }

      const cache = cacheRef.current;
      if (!cache) return;

      const defs = cache.listScenarios();
      if (defs.length === 0) return;

      const newResults = PROFILE_INDICES.map((pi) => {
        const result = interpolateScenarios(newState, defs, cache, pi);
        return result ? result.scenarioResult : null;
      });
      setMicroResults(computeDeltas(newResults));
    },
    [sliderState, computeDeltas],
  );

  // ── Drag end (macro projection) ──

  const handleDragEnd = useCallback(
    (key: string, value: number) => {
      const newState = { ...sliderState, [key]: value };
      setSliderState(newState);

      const cache = cacheRef.current;
      if (!cache) return;

      const defs = cache.listScenarios();
      if (defs.length === 0) return;

      const newResults = PROFILE_INDICES.map((pi) => {
        const result = interpolateScenarios(newState, defs, cache, pi);
        return result ? result.scenarioResult : null;
      });
      setMicroResults(computeDeltas(newResults));

      startTransition(() => setIsComputing(true));

      const orchestrator = orchestratorRef.current;
      if (orchestrator) {
        orchestrator.project(
          newState.ir / 100,
          newState.is / 100,
          5,
        ).then((result) => {
          if (result) setMacroResult(result);
          setIsComputing(false);
        });
      }
    },
    [sliderState, computeDeltas],
  );

  // ── Reset ──

  const handleReset = useCallback(() => {
    setSelectedScenarioId(null);
    setSliderState(DEFAULT_SLIDER_STATE);
    setAdvancedValues({});
    setMicroResults([null, null, null]);
    setMacroResult(null);
    setPhase('preselect');
    setAdvancedMode(false);
  }, []);

  // ── Toggle advanced ──

  const toggleAdvanced = useCallback(() => {
    setAdvancedMode((prev) => {
      if (prev) {
        // Exiting advanced: clear sub-param values
        setAdvancedValues({});
      } else {
        // Entering advanced: init sub-param values from current slider state
        const init: Record<string, number[]> = {};
        const s = sliderState;
        for (const key of Object.keys(LEVER_MAPPINGS)) {
          const mapping = LEVER_MAPPINGS[key];
          const mainVal = (s as unknown as Record<string, number>)[key] ?? 0;
          init[key] = mapping.subParams.map(() => mainVal);
        }
        setAdvancedValues(init);
      }
      return !prev;
    });
  }, [sliderState]);

  // ── Sub-slider change (advanced mode) ──

  const handleSubSliderChange = useCallback(
    (key: string, subIdx: number, value: number) => {
      const mapping = LEVER_MAPPINGS[key];
      if (!mapping) return;

      setAdvancedValues((prev) => {
        const updated = [...(prev[key] ?? mapping.subParams.map(() => 0))];
        updated[subIdx] = value;
        const newAv = { ...prev, [key]: updated };

        // Compute main slider as weighted average of sub-values
        let weightedSum = 0;
        for (let i = 0; i < updated.length; i++) {
          weightedSum += updated[i] * mapping.weights[i];
        }
        const mainVal = Math.round(weightedSum);

        setSliderState((s) => ({ ...s, [key]: mainVal }));
        return newAv;
      });

      // Trigger recomputation with the new main value
      const newState = { ...sliderState };
      let weightedSum = 0;
      const currentSubs = advancedValues[key] ?? mapping.subParams.map(() => 0);
      const updatedSubs = [...currentSubs];
      updatedSubs[subIdx] = value;
      for (let i = 0; i < updatedSubs.length; i++) {
        weightedSum += updatedSubs[i] * mapping.weights[i];
      }
      newState[key as keyof SliderState] = Math.round(weightedSum);

      const cache = cacheRef.current;
      if (!cache) return;

      const defs = cache.listScenarios();
      if (defs.length === 0) return;

      const newResults = PROFILE_INDICES.map((pi) => {
        const result = interpolateScenarios(newState, defs, cache, pi);
        return result ? result.scenarioResult : null;
      });
      setMicroResults(computeDeltas(newResults));
    },
    [sliderState, advancedValues, computeDeltas],
  );

  // ── Retry ──

  const retry = useCallback(() => {
    init();
  }, [init]);

  return {
    phase,
    scenarios,
    selectedScenarioId,
    sliderState,
    advancedValues,
    microResults,
    macroResult,
    isComputing: isComputing || isPending,
    errorMessage,
    loadProgress,
    advancedMode,
    init,
    selectScenario,
    handleSliderChange,
    handleSubSliderChange,
    handleDragEnd,
    handleReset,
    toggleAdvanced,
    retry,
  };
}
