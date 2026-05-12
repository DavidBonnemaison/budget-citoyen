# Règles fiscales — Budget Citoyen

Paramètres fiscaux et sociaux encodés au format OpenFisca-compatible YAML pour le simulateur Budget Citoyen.

## Structure

```
parameters/
├── ir/                    # Impôt sur le Revenu
│   ├── bareme.yaml        # Barème progressif (5 tranches, taux de 0% à 45%)
│   ├── deductions.yaml    # Déductions et abattements (frais professionnels)
│   ├── credits.yaml       # Crédits et réductions d'impôt
│   └── index.yaml         # Index du domaine IR
├── is/                    # Impôt sur les Sociétés
│   ├── taux.yaml          # Taux normal (25%), réduit PME (15%), contribution sociale
│   └── index.yaml
├── tva/                   # Taxe sur la Valeur Ajoutée
│   ├── taux.yaml          # Taux normal (20%), réduit (10%), super-réduit (5,5%), particulier (2,1%)
│   └── index.yaml
├── cotisations/           # Cotisations sociales
│   ├── salariales.yaml    # Part salariale (vieillesse, retraite complémentaire)
│   ├── patronales.yaml    # Part patronale (maladie, allocations familiales, chômage)
│   ├── csg_crds.yaml      # CSG (9,20%) et CRDS (0,50%)
│   └── index.yaml
└── aides/                 # Aides sociales
    ├── rsa.yaml           # Revenu de Solidarité Active
    ├── apl.yaml           # Aides Personnalisées au Logement
    ├── allocations_familiales.yaml
    ├── prime_activite.yaml
    └── index.yaml
variables/                 # Définitions de variables (contrat d'interface Phase 2)
reforms/                   # Scénarios de réforme pré-construits (vide en v1)
```

## Année de référence

Tous les paramètres sont verrouillés à l'année de référence **2025** (dernière année budgétaire complète avec données INSEE/CASD disponibles). Les dates dans les fichiers YAML utilisent exclusivement la clé `2025-01-01`.

## Sources législatives

Chaque paramètre référence l'article correspondant du code général des impôts, du code de la sécurité sociale ou du code de l'action sociale et des familles sur legifrance.gouv.fr. Les URL sont incluses dans le champ `metadata.reference` de chaque fichier YAML.

## Format

Les paramètres suivent le schéma OpenFisca :
- `description` : libellé du paramètre
- `metadata.reference` : URL de la source législative sur legifrance.gouv.fr
- `metadata.unit` : unité (`/1` pour un taux, `currency-EUR` pour un montant)
- `values.{date}.value` : valeur à une date donnée
- `brackets` : pour les paramètres par tranches (barème IR)

## Cadence de mise à jour

Alignée sur le cycle annuel du PLF (Projet de Loi de Finances). Le pipeline de données est ré-exécuté en septembre-octobre après publication des textes définitifs au Journal Officiel.

## Conversion YAML → JSON

Les fichiers YAML sont convertis en JSON au moment du build via le pipeline Python (`packages/data-pipeline/src/yaml2json/`). Le moteur WASM consomme exclusivement les fichiers JSON générés — aucune dépendance YAML n'est embarquée dans le binaire WASM.
