// webapp/src/state/index-map.ts
//
// Citizen lever-to-engine-parameter index mappings (D-08, D-12).
// Decision: public constant — no secrets, this is the "how it works" transparency.

// ── Types ──────────────────────────────────────────────────────────────────────

export interface LeverMapping {
  name: string;
  subParams: string[];
  weights: number[];
  baselineRate: number;
  rateFormat: 'percent' | 'currency' | 'none';
}

// ── Lever Mappings ────────────────────────────────────────────────────────────

/**
 * Mapping des 5 leviers citoyens vers les sous-paramètres du moteur microéconomique.
 *
 * Chaque levier contrôle un ensemble de sous-paramètres avec des proportions fixes.
 * Exemple: le levier "IR ménages" modifie les taux des 5 tranches proportionnellement
 * (20% de la variation sur chaque tranche).
 */
export const LEVER_MAPPINGS: Record<string, LeverMapping> = {
  ir: {
    name: 'IR ménages',
    subParams: [
      'ir.bareme.tranche1',
      'ir.bareme.tranche2',
      'ir.bareme.tranche3',
      'ir.bareme.tranche4',
      'ir.bareme.tranche5',
    ],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  is: {
    name: 'IS entreprises',
    subParams: ['is.taux'],
    weights: [1.0],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  tva: {
    name: 'TVA',
    subParams: ['tva.taux.normal', 'tva.taux.reduit'],
    weights: [0.7, 0.3],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  cotisations: {
    name: 'Cotisations sociales',
    subParams: [
      'cotisations.salariales',
      'cotisations.patronales',
      'cotisations.csg_crds',
    ],
    weights: [0.35, 0.35, 0.3],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  depenses: {
    name: 'Dépenses publiques',
    subParams: ['depenses.spend_level', 'depenses.effectifs'],
    weights: [0.7, 0.3],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
};
