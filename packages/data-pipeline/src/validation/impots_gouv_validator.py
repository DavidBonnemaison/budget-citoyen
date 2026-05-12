"""Manual validation protocol for impots.gouv.fr simulator (D-12).

Documents the step-by-step process for manually validating 10-20 canonical
household profiles on the official French tax simulator, capturing results
for comparison with openfisca-france and the WASM engine.

Per D-12: impots.gouv.fr provides the authoritative ground truth for
household-level tax computation. Until programmatic API access is confirmed
(RESEARCH.md §Open Questions #4), manual validation of all 16 profiles is the
baseline protocol. The validation involves navigating the simulator, entering
profile data, capturing results, and recording them in structured CSV format.
"""

VALIDATION_PROTOCOL = """
# Protocole de Validation — Simulateur impots.gouv.fr

## Objectif

Valider les 16 profils canoniques sur le simulateur officiel de la DGFiP
afin d'établir les valeurs de référence pour le cadre de validation bilingue.

## Prérequis

- Navigateur web moderne (Chrome, Firefox, ou Safari)
- Accès à https://www.impots.gouv.fr/simulateurs
- Fichier de référence : `canonical_profiles.py` dans packages/data-pipeline/src/validation/
- Tableur pour la capture des résultats (format CSV)

## Étapes par profil

Pour chaque profil canonique (16 profils dans CANONICAL_PROFILES) :

### 1. Navigation
   1. Aller sur https://www.impots.gouv.fr/simulateurs
   2. Sélectionner le simulateur "Impôt sur le revenu"
   3. Choisir l'année de référence : **2025** (revenus 2024)
   4. Sélectionner la situation familiale correspondant au profil

### 2. Saisie des données démographiques
   - **Situation familiale** : mapper `situation_familiale` du profil vers
     l'interface (célibataire → C, marié → M, pacsé → P, divorcé → D)
   - **Nombre d'enfants à charge** : `nb_enfants` du profil
   - **Zone de résidence** : la zone (`zone1`/`zone2`/`zone3`) n'affecte
     pas le simulateur IR — noter pour les APL

### 3. Saisie des revenus
   - **Salaires** : saisir le total des `revenus.salaires` dans la case
     "Traitements et salaires" (1AJ pour le déclarant 1)
   - **Pensions** : saisir `revenus.pensions` dans "Pensions et retraites"
   - **BNC** : `revenus.bnc` → "Bénéfices non commerciaux"
   - **BIC** : `revenus.bic` → "Bénéfices industriels et commerciaux"
   - **Revenus fonciers** : `revenus.fonciers` → "Revenus fonciers"
   - **Allocations chômage** : `revenus.allocations_chomage` → case 1AP/1BP

### 4. Capture des résultats
   1. Cliquer sur "Calculer" ou "Simuler"
   2. Noter les résultats affichés :
      - **Impôt sur le revenu net** (avant crédits d'impôt)
      - **Revenu fiscal de référence** (RFR)
      - **Nombre de parts** (quotient familial calculé)
      - **Taux marginal d'imposition**
   3. **Capture d'écran** : sauvegarder sous `screenshots/{profile_name}.png`
      (convention de nommage)

### 5. Enregistrement
   Saisir les résultats dans le fichier CSV :
   ```
   profile_name, ir_net, rfr, nb_parts, tmi, date_validation, validateur
   ```

## Conventions de nommage des captures d'écran

```
screenshots/
  ├── celibataire_smic.png
  ├── celibataire_cadre.png
  ├── celibataire_retraite.png
  ├── etudiant.png
  ├── chomeur.png
  ├── couple_bi_actif.png
  ├── couple_mono_actif.png
  ├── couple_retraite.png
  ├── pacse_sans_enfant.png
  ├── famille_nombreuse.png
  ├── famille_monoparentale.png
  ├── independant_bnc.png
  ├── independant_bic.png
  ├── multi_proprietaire.png
  ├── etranger_resident.png
  └── haut_revenu.png
```

## Format des résultats attendus

Pour chaque profil, les résultats validés doivent être intégrés dans le champ
`expected_results.impots_gouv_fr` du profil dans `canonical_profiles.py` :

```python
"expected_results": {
    "impots_gouv_fr": {
        "ir_net": 1234.00,           # Impôt net (avant crédits)
        "rfr": 45678.00,             # Revenu fiscal de référence
        "nb_parts": 2.5,             # Quotient familial calculé
        "tmi": "30%",                # Taux marginal d'imposition
        "validated_at": "2026-05-XX", # Date de validation
        "validated_by": "Nom",       # Personne ayant fait la validation
    },
    "openfisca_reference": { ... },  # Rempli automatiquement par reference_sim.py
}
```

## Contrôle de cohérence

Après validation, vérifier pour chaque profil :
1. **Différence IR** : `|ir_impots_gouv - ir_openfisca|` < seuil toléré
   (1€ de différence toléré pour les arrondis d'affichage ; précision
   réelle vérifiée à 1e-6 en interne D-13)
2. **Nombre de parts** : Le nombre de parts calculé par impots.gouv.fr
   doit correspondre à `_compute_quotient_familial()` dans reference_sim.py
3. **Incohérences** : Toute divergence > 5% doit être documentée et
   investiguée (erreur de saisie, paramètre manquant, différence de barème)

## Limitations connues

- Le simulateur impots.gouv.fr peut utiliser des paramètres légèrement
  différents de openfisca-france (arrondis, règles d'abattement spécifiques)
- L'absence d'API programmatique signifie que ce processus est manuel et
  sujet aux erreurs de saisie (mitigé par la capture d'écran)
- Le simulateur ne couvre que l'IR — les cotisations sociales, la CSG/CRDS,
  et les aides sociales doivent être validées séparément via openfisca-france
"""

# Convenience accessor for the validation protocol string
def get_validation_protocol() -> str:
    """Return the full validation protocol as a Markdown string."""
    return VALIDATION_PROTOCOL.strip()
