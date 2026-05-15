// webapp/src/engine/types.ts
//
// Central TypeScript type definitions for Budget Citoyen engines.
// Mirrors the deprecated Rust core crate types (packages/core/src/types.rs)
// with zero runtime dependencies — pure TypeScript interfaces only.
//
// These types replace the WASM-bound types from the deleted wasm-micro and
// wasm-macro crates. Data arrives via postMessage Transferable (D-12) —
// no fetch(), no WASM imports, no runtime dependencies.

// ── Macroeconomic Result (mirrors Rust MacroResult) ────────────────────────

/**
 * Résultat d'une projection macroéconomique.
 *
 * NOTE: This interface uses JS camelCase naming conventions.
 * Rust equivalent (packages/core/src/types.rs:MacroResult) uses snake_case.
 * These types are independent — no WASM serialization contract exists between them.
 *
 * All trajectory arrays have the same length (1 for single-point interpolation,
 * N for N-year projection).
 */
export interface MacroResult {
  /** Trajectoire du déficit public (points de PIB par année). */
  deficitTrajectory: number[];
  /** Trajectoire de la dette publique (% du PIB par année). */
  debtTrajectory: number[];
  /** Trajectoire de la croissance du PIB (% par année). */
  gdpGrowthTrajectory: number[];
  /** Trajectoire de l'emploi (milliers par année). */
  employmentTrajectory: number[];
  /** Indique si les paramètres sortent du domaine de validité de la matrice. */
  isOutOfBounds: boolean;
  /** Message d'avertissement lorsque isOutOfBounds est true. */
  warningMessage: string | null;
}

// ── Microeconomic / Scenario Result ─────────────────────────────────────────

/**
 * Résultat d'une simulation microéconomique pour un profil donné.
 *
 * Replaces the WASM MicroResult in the new hybrid architecture.
 * Pre-computed scenario results are loaded from JSON and cached for O(1) lookup.
 */
export interface ScenarioResult {
  /** Impôt sur le revenu. */
  ir: number;
  /** Impôt sur les sociétés (contribution du profil). */
  is: number;
  /** TVA acquittée. */
  tva: number;
  /** Cotisations sociales totales (salariales + patronales + CSG/CRDS). */
  cotisations: number;
  /** Aides sociales reçues (total). */
  aides: number;
  /** Revenu disponible après impôts et transferts. */
  revenuDisponible: number;
}

/**
 * Définition d'un scénario fiscal (paramètres de réforme).
 *
 * Chaque scénario correspond à une combinaison de curseurs budgétaires
 * pour laquelle les résultats micro sont pré-calculés.
 */
export interface ScenarioDefinition {
  /** Identifiant unique du scénario (ex: "baseline-2025", "reform-tva-22"). */
  id: string;
  /** Nom lisible du scénario. */
  name: string;
  /** Description textuelle de la réforme. */
  description: string;
  /** Overrides de paramètres (clé → valeur). Les clés non spécifiées
   * conservent leur valeur par défaut. */
  parameterOverrides: Record<string, unknown>;
}

// ── Shock Matrix Data (transferred via ArrayBuffer) ─────────────────────────

/**
 * Matrice des chocs macroéconomiques pré-calculée.
 *
 * Toutes les propriétés numériques utilisent Float64Array pour permettre
 * le transfert zero-copy via postMessage (D-12).
 *
 * La grille est un tenseur 4D aplati en ordre row-major:
 *   grid[((taxIdx * spendBp.length + spendIdx) * horizonBp.length + horizonIdx) * 4 + featureIdx]
 * où featureIdx: 0=croissance PIB, 1=emploi, 2=déficit, 3=dette.
 *
 * Les équations de l'enveloppe convexe sont stockées à plat par stride de 4:
 *   [a1, a2, a3, b] pour chaque hyperplan, définissant a1*tax + a2*spend + a3*horizon + b ≤ 0.
 */
export interface ShockMatrixData {
  /** Grille 4D aplatie: tax × spend × horizon × feature (4 features). */
  grid: Float64Array;
  /** Points de rupture de la dimension fiscale (taux d'imposition). */
  taxBp: Float64Array;
  /** Points de rupture de la dimension dépenses publiques. */
  spendBp: Float64Array;
  /** Points de rupture de la dimension horizon temporel (années). */
  horizonBp: Float64Array;
  /** Équations des hyperplans de l'enveloppe convexe (stride 4). */
  hullEquations: Float64Array;
}

// ── Worker Message Protocol (D-11 — correlation IDs) ──────────────────────

/** Types de messages supportés par le protocole Worker. */
export type WorkerMessageType =
  | 'INIT'
  | 'SIMULATE'
  | 'INTERPOLATE'
  | 'PROJECT'
  | 'READY'
  | 'CITIZEN_RESULT'
  | 'MACRO_RESULT'
  | 'ERROR';

/**
 * Requête envoyée par l'orchestrateur à un Worker.
 *
 * D-11: Chaque requête porte un `id` unique (crypto.randomUUID())
 * pour le protocole de corrélation et le rejet des réponses périmées.
 */
export interface WorkerRequest {
  /** Identifiant de corrélation (crypto.randomUUID()). */
  id: string;
  /** Type de l'opération demandée. */
  type: WorkerMessageType;
  /** Charge utile spécifique au type d'opération. */
  payload: unknown;
}

/**
 * Réponse renvoyée par un Worker à l'orchestrateur.
 *
 * D-11: Le champ `id` fait écho à l'identifiant de la requête d'origine.
 * Les réponses dont l'ID ne correspond pas à la dernière requête en cours
 * sont rejetées (stale response discarding).
 */
export interface WorkerResponse<T = unknown> {
  /** Identifiant de corrélation (écho de la requête d'origine). */
  id: string;
  /** Type de la réponse. */
  type: WorkerMessageType;
  /** Charge utile ou null en cas d'absence de donnée. */
  payload: T | null;
}

// ── Payload Types ───────────────────────────────────────────────────────────

/** Charge utile d'une requête SIMULATE (citizen-worker). */
export interface SimulatePayload {
  /** Identifiant du scénario pré-calculé (ex: "baseline-2025"). */
  scenarioId: string;
  /** Index du profil dans la population synthétique (0-49999). */
  profileIndex: number;
}

/** Charge utile d'une requête INIT pour le citizen-worker. */
export interface CitizenInitPayload {
  /** Données de scénarios pré-calculés au format JSON. */
  scenariosJson: string;
}

/** Charge utile d'une requête INIT pour le macro-worker. */
export interface MacroInitPayload {
  /** Matrice des chocs sérialisée en binaire (ArrayBuffer transférable). */
  matrixBytes: ArrayBuffer;
}

/** Charge utile d'une requête INTERPOLATE (macro-worker, point unique). */
export interface InterpolatePayload {
  /** Taux d'imposition (curseur macro). */
  tax: number;
  /** Niveau de dépenses publiques (curseur macro). */
  spend: number;
  /** Année d'horizon pour l'interpolation (1-5). */
  horizon: number;
  /** Sous-type d'opération. */
  subType?: 'interpolate';
}

/** Charge utile d'une requête PROJECT (macro-worker, trajectoire). */
export interface ProjectPayload {
  /** Taux d'imposition (curseur macro). */
  tax: number;
  /** Niveau de dépenses publiques (curseur macro). */
  spend: number;
  /** Nombre d'années à projeter. */
  years: number;
  /** Sous-type d'opération. */
  subType: 'project';
}

// ── Result type aliases ─────────────────────────────────────────────────────

/** Résultat d'une requête SIMULATE. */
export type CitizenResult = ScenarioResult;

/** Résultat d'une requête INTERPOLATE ou PROJECT (null si hors domaine). */
export type MacroWorkerResult = MacroResult | null;
