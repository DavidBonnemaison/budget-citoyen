// webapp/src/hooks/useSimulation.ts
//
// Central simulation hook: state machine (LOADING→PRESELECT→DISPLAYING→ERROR),
// WorkerOrchestrator coordination, interpolation, URL state restore (D-07, D-15, D-23).
// Decision: main-thread interpolation for MVP (OQ3 — simpler and <1ms per call).

import { useState, useRef, useCallback, useEffect, useTransition } from 'react';
import { WorkerOrchestrator } from '../workers/orchestrator';
import { ScenarioCache } from '../engine/scenario-cache';
import { interpolateScenarios } from '../state/interpolation';
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
  microResults: (ScenarioResult | null)[];
  macroResult: MacroResult | null;
  isComputing: boolean;
  errorMessage: string | null;
  loadProgress: LoadProgress;
  advancedMode: boolean;
  init: () => Promise<void>;
  selectScenario: (id: string) => Promise<void>;
  handleSliderChange: (key: string, value: number) => void;
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
  const [isPending, startTransition] = useTransition();

  const orchestratorRef = useRef<WorkerOrchestrator | null>(null);
  const cacheRef = useRef<ScenarioCache | null>(null);

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
      const matrixResponse = await fetch('/data/shock-matrix-v2025.1.bin');
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
              orchestrator.project(restored.p.ir, restored.p.is, 5).then(setMacroResult);
            }
          } else {
            setPhase('preselect');
          }
          setLoadProgress({ phase: 'Prêt', percent: 100 });
          return;
        }
      }

      setLoadProgress({ phase: 'Prêt', percent: 100 });
      setPhase('preselect');
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Erreur inconnue');
      setPhase('error');
    }
  }, []);

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
        setMicroResults(results);

        // Set sliders from scenario overrides
        const def = cache.listScenarios().find((s) => s.id === id);
        if (def) {
          setSliderState({
            ir: def.parameterOverrides['ir'] ?? 0,
            is: def.parameterOverrides['is'] ?? 0,
            tva: def.parameterOverrides['tva'] ?? 0,
            cotisations: def.parameterOverrides['cotisations'] ?? 0,
            depenses: def.parameterOverrides['depenses'] ?? 0,
          });
        }

        // Initial macro projection
        orchestrator.project(0, 0, 5).then((result) => {
          if (result) setMacroResult(result);
        });
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : 'Erreur de simulation');
        setPhase('error');
      }
    },
    [],
  );

  // ── Slider change ──

  const handleSliderChange = useCallback(
    (key: string, value: number) => {
      const newState = { ...sliderState, [key]: value };
      setSliderState(newState);

      const cache = cacheRef.current;
      if (!cache) return;

      // Interpolate for each profile
      const defs = cache.listScenarios();
      if (defs.length === 0) return;

      const newResults = PROFILE_INDICES.map((pi) => {
        const result = interpolateScenarios(newState, defs, cache, pi);
        return result ? result.scenarioResult : null;
      });
      setMicroResults(newResults);
    },
    [sliderState],
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
      setMicroResults(newResults);

      startTransition(() => setIsComputing(true));

      const orchestrator = orchestratorRef.current;
      if (orchestrator) {
        orchestrator.project(newState.ir, newState.is, 5).then((result) => {
          if (result) setMacroResult(result);
          setIsComputing(false);
        });
      }
    },
    [sliderState],
  );

  // ── Reset ──

  const handleReset = useCallback(() => {
    setSelectedScenarioId(null);
    setSliderState(DEFAULT_SLIDER_STATE);
    setMicroResults([null, null, null]);
    setMacroResult(null);
    setPhase('preselect');
    setAdvancedMode(false);
  }, []);

  // ── Toggle advanced ──

  const toggleAdvanced = useCallback(() => {
    setAdvancedMode((prev) => !prev);
  }, []);

  // ── Retry ──

  const retry = useCallback(() => {
    init();
  }, [init]);

  return {
    phase,
    scenarios,
    selectedScenarioId,
    sliderState,
    microResults,
    macroResult,
    isComputing: isComputing || isPending,
    errorMessage,
    loadProgress,
    advancedMode,
    init,
    selectScenario,
    handleSliderChange,
    handleDragEnd,
    handleReset,
    toggleAdvanced,
    retry,
  };
}
