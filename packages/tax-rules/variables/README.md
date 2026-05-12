# Variables

Ce répertoire contiendra les définitions de variables (au sens OpenFisca) qui composent les formules de calcul à partir des paramètres.

Les variables documentent les relations entre paramètres (ex: `ir_brut = somme des tranches × taux`), servent de contrat d'interface pour le portage Rust/WASM en Phase 2, et seront utilisées par le framework de validation bilingue (Plan 04).

**Statut du répertoire (Phase 1 — Plan 01):** Créé en prévision des implémentations futures. Les variables seront définies dans le Plan 04 (bilingual validation) en utilisant `openfisca-france` comme référence.

## Format attendu

Chaque variable suit la convention OpenFisca :
```yaml
description: Libellé de la variable
formula: expression mathématique ou référence aux paramètres
inputs:
  - parametre_source_1
  - parametre_source_2
output:
  type: float
  unit: currency-EUR
```
