// webapp/src/state/types.ts
//
// UI state type definitions for the Budget Citoyen interactive shell.
// Decision: pure TypeScript interfaces — no runtime code, only import type from engine.

import type { ScenarioResult, ScenarioDefinition } from '../engine/types';

// ── Slider State ──────────────────────────────────────────────────────────────

/** Positions des 5 curseurs budgétaires citoyens. Toutes les valeurs sont des nombres. */
export interface SliderState {
  ir: number;
  is: number;
  tva: number;
  cotisations: number;
  depenses: number;
}

// ── URL State ─────────────────────────────────────────────────────────────────

/** État sérialisé dans l'URL pour le partage (D-23).
 *  s: scenarioId sélectionné (null si aucun scénario)
 *  p: positions des curseurs
 *  f: index du profil affiché actuellement (0=modeste, 1=médian, 2=aisé)
 *  a: mode avancé activé (true = sliders individuels visibles) */
export interface URLState {
  s: string | null;
  p: SliderState;
  f: number;
  a: boolean;
}

// ── Interpolation Result ──────────────────────────────────────────────────────

/** Résultat d'une interpolation entre scénarios (D-01, D-02). */
export interface InterpolationResult {
  scenarioResult: ScenarioResult;
  sourceScenarios: string[];
  weights: number[];
  isExact: boolean;
}

// ── Lever-to-Parameter Mapping ────────────────────────────────────────────────

/** Mapping d'un levier citoyen vers les sous-paramètres du moteur (D-08, D-12). */
export interface ParameterMapping {
  citizenLever: string;
  parameterKeys: string[];
  proportions: number[];
}
