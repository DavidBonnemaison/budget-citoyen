---
phase: 01-data-foundation-rules-engine
plan: 05
type: execute
wave: 1
depends_on: []
files_modified:
  # Task 1 — IR, IS, TVA
  - packages/tax-rules/parameters/ir/quotient_familial.yaml
  - packages/tax-rules/parameters/ir/decote.yaml
  - packages/tax-rules/parameters/ir/plafonnement_qf.yaml
  - packages/tax-rules/parameters/ir/cehr.yaml
  - packages/tax-rules/parameters/ir/credits.yaml
  - packages/tax-rules/parameters/ir/index.yaml
  - packages/tax-rules/parameters/is/exonerations.yaml
  - packages/tax-rules/parameters/is/report_deficits.yaml
  - packages/tax-rules/parameters/is/CVAE.yaml
  - packages/tax-rules/parameters/is/index.yaml
  - packages/tax-rules/parameters/tva/franchise.yaml
  - packages/tax-rules/parameters/tva/exonerations.yaml
  - packages/tax-rules/parameters/tva/index.yaml
  # Task 2 — Cotisations, Aides
  - packages/tax-rules/parameters/cotisations/allegements_fillon.yaml
  - packages/tax-rules/parameters/cotisations/forfait_social.yaml
  - packages/tax-rules/parameters/cotisations/pass.yaml
  - packages/tax-rules/parameters/cotisations/index.yaml
  - packages/tax-rules/parameters/aides/aah.yaml
  - packages/tax-rules/parameters/aides/aspa.yaml
  - packages/tax-rules/parameters/aides/css.yaml
  - packages/tax-rules/parameters/aides/cheque_energie.yaml
  - packages/tax-rules/parameters/aides/allocation_rentree_scolaire.yaml
  - packages/tax-rules/parameters/aides/paje.yaml
  - packages/tax-rules/parameters/aides/are.yaml
  - packages/tax-rules/parameters/aides/index.yaml
  # Task 3 — Canonical profiles
  - packages/data-pipeline/src/validation/canonical_profiles.py
  - packages/data-pipeline/tests/test_validation.py
autonomous: true
requirements: [DATA-01]
gap_closure: true

must_haves:
  truths:
    - "All 30+ YAML parameter files across 5 domains parse without error via yaml.safe_load()"
    - "YAML→JSON conversion pipeline produces valid JSON for all parameter files without schema violations"
    - "credits.yaml contains 25+ tax credit entries with legifrance.gouv.fr legislation references"
    - "32 canonical profiles exist with all required fields (name, description, situation_familiale, nb_enfants, revenus, patrimoine, zone_residence) and unique names"
    - "Canonical profiles cover all 7 gap-diagnosis dimensions: income stratification, family structures, zone residence, asset profiles, profession types, social benefit edge cases, cross-category combinations"
    - "test_profile_count_at_least_fourteen passes with updated ≥30 threshold"
    - "All 5 domain index.yaml files reference their complete parameter file inventories"
  artifacts:
    - path: "packages/tax-rules/parameters/ir/quotient_familial.yaml"
      provides: "Quotient familial parts computation parameters"
      contains: "metadata.reference"
    - path: "packages/tax-rules/parameters/ir/decote.yaml"
      provides: "Décote mechanism for low-income IR elimination"
    - path: "packages/tax-rules/parameters/ir/plafonnement_qf.yaml"
      provides: "Cap on quotient familial tax advantage per half-part"
    - path: "packages/tax-rules/parameters/ir/cehr.yaml"
      provides: "Contribution Exceptionnelle sur les Hauts Revenus"
    - path: "packages/tax-rules/parameters/ir/credits.yaml"
      provides: "25+ crédits et réductions d'impôt"
    - path: "packages/tax-rules/parameters/is/exonerations.yaml"
      provides: "IS exonérations (PME, JEI, zones)"
    - path: "packages/tax-rules/parameters/is/report_deficits.yaml"
      provides: "Carryback/carryforward deficit rules"
    - path: "packages/tax-rules/parameters/is/CVAE.yaml"
      provides: "Cotisation sur la Valeur Ajoutée des Entreprises parameters"
    - path: "packages/tax-rules/parameters/tva/franchise.yaml"
      provides: "Franchise en base TVA thresholds"
    - path: "packages/tax-rules/parameters/tva/exonerations.yaml"
      provides: "TVA exonérations sectorielles"
    - path: "packages/tax-rules/parameters/cotisations/allegements_fillon.yaml"
      provides: "Réduction générale cotisations patronales (ex-Fillon)"
    - path: "packages/tax-rules/parameters/cotisations/forfait_social.yaml"
      provides: "Forfait social rates and exemptions"
    - path: "packages/tax-rules/parameters/cotisations/pass.yaml"
      provides: "Plafond Annuel de la Sécurité Sociale 2025"
    - path: "packages/tax-rules/parameters/aides/aah.yaml"
      provides: "Allocation aux Adultes Handicapés"
    - path: "packages/tax-rules/parameters/aides/aspa.yaml"
      provides: "Allocation de Solidarité aux Personnes Âgées"
    - path: "packages/tax-rules/parameters/aides/css.yaml"
      provides: "Complémentaire Santé Solidaire"
    - path: "packages/tax-rules/parameters/aides/cheque_energie.yaml"
      provides: "Chèque énergie eligibility brackets"
    - path: "packages/tax-rules/parameters/aides/allocation_rentree_scolaire.yaml"
      provides: "ARS amounts by age and income ceilings"
    - path: "packages/tax-rules/parameters/aides/paje.yaml"
      provides: "Prestation d'Accueil du Jeune Enfant components"
    - path: "packages/tax-rules/parameters/aides/are.yaml"
      provides: "Allocation de Retour à l'Emploi calculation rules"
    - path: "packages/data-pipeline/src/validation/canonical_profiles.py"
      provides: "32 canonical household profiles"
      min_items: 32
    - path: "packages/data-pipeline/tests/test_validation.py"
      provides: "Profile count assertion updated ≥30"
  key_links:
    - from: "packages/tax-rules/parameters/ir/credits.yaml"
      to: "packages/data-pipeline/src/yaml2json/convert.py"
      via: "YAML→JSON pipeline"
      pattern: "yaml\\.safe_load.*credits\\.yaml"
    - from: "packages/tax-rules/parameters/{domain}/index.yaml"
      to: "packages/tax-rules/parameters/{domain}/*.yaml"
      via: "file reference in parameters list"
      pattern: "file:.*\\.yaml"
    - from: "packages/data-pipeline/src/validation/canonical_profiles.py"
      to: "packages/data-pipeline/tests/test_validation.py"
      via: "import CANONICAL_PROFILES + len assertion"
      pattern: "CANONICAL_PROFILES"
---

<objective>
Close Phase 1 UAT gaps #1 (YAML parameter completeness) and #2 (canonical profiles depth) diagnosed in 01-UAT.md.

**Gap #1 — YAML parameter completeness:** Expand from 12 to 30+ parameter files across all 5 tax domains. The starter skeleton delivered structural quality (format, references, validation gate) but only ~20-25% semantic coverage. IR domain cannot compute without quotient_familial, decote, plafonnement_qf, CEHR. Aides domain is missing AAH, ASPA, CSS, ARE. Cotisations missing allègements Fillon and forfait social. Only 3 of ~474 dépenses fiscales are modeled.

**Gap #2 — Canonical profiles depth:** Expand from 16 to 32 profiles with systematic coverage across 7 diagnostic dimensions: income stratification, family structures, zone residence, asset profiles, profession types, social benefit edge cases, cross-category combinations. Current coverage thinly addresses D-12 edge cases (7 of 8 cases have only 1-2 profiles), missing CEHR threshold profiles, single-parent+1-child, zone3 at multiple income points, and cross-category intersections.

Purpose: Phase 2's WASM microsimulation engine needs semantically complete parameter data to compute valid IR, IS, TVA, cotisations, and aides for any profile. Phase 2's bilingual validation framework needs dense canonical profiles hitting all critical fiscal thresholds (CEHR, IR brackets, QF caps, décote).
Output: 18+ new YAML parameter files, 5 updated domain index files, expanded credits.yaml (25+ entries), 32 canonical profiles in canonical_profiles.py, updated test threshold (≥30).
</objective>

<execution_context>
@/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/user/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-data-foundation-rules-engine/01-01-SUMMARY.md
@.planning/phases/01-data-foundation-rules-engine/01-04-SUMMARY.md
@.planning/phases/01-data-foundation-rules-engine/01-UAT.md (gap diagnoses)

<interfaces>
<!-- Key types and contracts the executor needs. Extracted from existing codebase. -->

From packages/data-pipeline/src/schemas/parameter.schema.json (Draft 2020-12):
- Required: `description` (string), plus either `values` or `brackets`
- `values`: date-keyed object with pattern `^\d{4}-\d{2}-\d{2}$`, each containing `value` (number|null|object)
- `brackets`: array of `{threshold, rate}` objects, each with `description`, `values` sub-objects

From packages/tax-rules/parameters/ir/bareme.yaml — Established YAML authoring pattern:
```yaml
description: <human-readable>
metadata:
  reference: https://www.legifrance.gouv.fr/...
  unit: /1  # or currency-EUR
brackets:  # OR values: for non-progressive parameters
  - threshold:
      description: ...
      values:
        2025-01-01:
          value: <number>
    rate:
      description: ...
      values:
        2025-01-01:
          value: <number>
```

From packages/tax-rules/parameters/ir/credits.yaml — established multi-entry values pattern:
```yaml
values:
  2025-01-01:
    value:
      entry_name:
        taux: <float>
        plafond: <number>
        description: ...
        reference: https://www.legifrance.gouv.fr/...
```

From packages/data-pipeline/src/validation/canonical_profiles.py — established profile dict schema:
```python
{"name": "profile_id",
 "description": "...",
 "situation_familiale": "celibataire|marie|divorce|pacse|veuf",
 "nb_enfants": int,
 "revenus": {"salaires": [], "pensions": [], "bnc": [], "fonciers": [], ...},
 "patrimoine": {"immobilier": float, "financier": float},
 "zone_residence": "zone1|zone2|zone3",
 "expected_results": {"impots_gouv_fr": {}, "openfisca_reference": {}}}
```

From packages/data-pipeline/tests/test_validation.py — test threshold pattern:
```python
def test_profile_count_at_least_fourteen(self):
    count = len(CANONICAL_PROFILES)
    assert count >= 14, (...)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Expand IR, IS, TVA YAML parameter files + credits.yaml to 25+ entries</name>
  <files>
    packages/tax-rules/parameters/ir/quotient_familial.yaml
    packages/tax-rules/parameters/ir/decote.yaml
    packages/tax-rules/parameters/ir/plafonnement_qf.yaml
    packages/tax-rules/parameters/ir/cehr.yaml
    packages/tax-rules/parameters/ir/credits.yaml
    packages/tax-rules/parameters/ir/index.yaml
    packages/tax-rules/parameters/is/exonerations.yaml
    packages/tax-rules/parameters/is/report_deficits.yaml
    packages/tax-rules/parameters/is/CVAE.yaml
    packages/tax-rules/parameters/is/index.yaml
    packages/tax-rules/parameters/tva/franchise.yaml
    packages/tax-rules/parameters/tva/exonerations.yaml
    packages/tax-rules/parameters/tva/index.yaml
  </files>
  <action>
    Create 9 new YAML parameter files and expand credits.yaml from 3 to 25 entries, then update 3 domain index.yaml files. All files follow the OpenFisca-compatible pattern established in 01-01-SUMMARY.md: `description` at top, `metadata.reference` pointing to legifrance.gouv.fr, `values` date-keyed to `2025-01-01`, and either scalar values or nested object structures.

    **IR domain — 4 new files + 1 expanded:**

    1. **quotient_familial.yaml** (values type, unit: /1): Parts de quotient familial. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052191. Under values.2025-01-01.value:
       - `celibataire_divorce_veuf` (1 part base), `celibataire_1_enfant` (1.5), `celibataire_2_enfants` (2.0), `celibataire_3_enfants` (2.5), `celibataire_4_enfants` (3.0) — formula: 1 + 0.5 per child (first 2 count as 0.5 each, 3rd+ as 1)
       - `couple_marie_pacse` (2 parts base), `couple_1_enfant` (2.5), `couple_2_enfants` (3.0), `couple_3_enfants` (4.0), `couple_4_enfants` (5.0)
       - `parent_isole` base: 1 + 0.5 majoration + 0.5 per child (first child gives 2.0 total parts)
       - `personne_invalide` majoration: +0.5 part supplémentaire
       - `ancien_combattant` majoration: +0.5 part
       - `veuf_avec_enfant` majoration: additional parts equivalent to married couple regime
       - `plafond_avantage_fiscal` (1,759 € maximum tax reduction per half-part 2025, for reference)
       - `plafond_parent_isole_1er_enfant` (4,149 €)
       - `plafond_veuf_enfant` (4,149 €)
       - `plafond_invalidite` (3,512 €)

    2. **decote.yaml** (values type, unit: currency-EUR): Mécanisme de décote pour élimination IR petits montants. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052191. Under values.2025-01-01.value:
       - `celibataire_plafond` (873 € — IR threshold below which décote eliminates tax)
       - `celibataire_taux` (0.4525 — fraction of IR used in décote formula)
       - `couple_plafond` (1,449 €)
       - `couple_taux` (0.4525)
       - `formule`: "décote = plafond - taux × IR_brut; if IR_brut - décote ≤ 0 then IR_net = 0"

    3. **plafonnement_qf.yaml** (values type, unit: currency-EUR): Plafonnement des effets du quotient familial. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052193. Under values.2025-01-01.value:
       - `plafond_general_demi_part` (1,759 € — 2025 general cap per half-part)
       - `plafond_parent_isole` (4,149 € — for first child of parent isolé)
       - `plafond_veuf_enfant` (4,149 €)
       - `plafond_invalidite` (3,512 €)
       - `plafond_ancien_combattant` (1,759 €)

    4. **cehr.yaml** (brackets type, unit: /1): Contribution exceptionnelle sur les hauts revenus. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053002. Uses brackets structure (like bareme.yaml) with 2 brackets:
       - Bracket 1: threshold 250,000 € (célibataire/divorcé/veuf) / 500,000 € (couple), rate 0.03
       - Bracket 2: threshold 500,000 € (célibataire) / 1,000,000 € (couple), rate 0.04
       - Note in each threshold description: the couple threshold is doubled. Add `threshold_couple` and `threshold_celibataire` sub-values.

    5. **credits.yaml** (expand existing — keep current 3 entries, add 22 new. Total = 25): Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052888. Expand the `values.2025-01-01.value` object with these additional entries (each with `taux`, `plafond` or `plafond_pct_rfr`, `description`, and `reference` fields):
       - `scolarite_enfants`: college (61 €), lycee (153 €), superieur (183 €) — per child flat amounts. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052930
       - `frais_garde_enfants_hors_domicile`: taux 0.50, plafond 12000 (shared cap with emploi_domicile may overlap). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052930
       - `transition_energetique_ma_prime_renov`: multi-tier subsidies, store as `taux_variable: true, paliers: [{rfr_par_uc_max, taux_ecogeste}]` structure. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053102
       - `investissement_locatif_pinel`: taux 0.105/0.15/0.175/0.21 for 6/9/12-year commitments, plafond 300000. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052956
       - `investissement_locatif_denormandie`: taux 0.12/0.18/0.21, plafond 300000. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052958
       - `souscription_capital_pme`: taux 0.18, plafond 50000 (célibataire) / 100000 (couple). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052962
       - `souscription_fip_fcpi`: taux 0.18 (standard) / 0.25 (Corse/Outre-mer), plafond 12000/24000. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052964
       - `cotisations_syndicales`: taux 0.66, plafond_pct_salaire 0.01. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052942
       - `frais_dependance`: taux 0.25, plafond 10000. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052944
       - `prestation_compensatoire`: taux 0.25, plafond 30500. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052946
       - `investissement_outre_mer_logement`: taux 0.23 to 0.29 (varies by sector/fiscal year), plafond varies. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052968
       - `investissement_outre_mer_productif`: taux 0.30 to 0.45. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052970
       - `mecenat_entreprise`: taux 0.60, plafond_pct_ca 0.005. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052972
       - `monuments_historiques`: taux 0.50 (ouvert au public) / 1.00 (non ouvert), sans plafond IR mais plafonnement global niches 10000. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052974
       - `sofica`: taux 0.30/0.36/0.48, plafond_pct_rfr 0.25. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052976
       - `investissement_foret`: taux 0.18, plafond varies. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052978
       - `compte_pme_investissement`: taux 0.18, plafond varies. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052962 (shared with IR-PME)
       - `souscription_entreprise_solidaire`: taux 0.25, plafond varies. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052980
       - `cotisations_organismes_interet_general`: taux 0.66, plafond_pct_rfr 0.20 (shared cap with dons_associations). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052888
       - `abonnement_transports_publics`: taux 0.50, employee-only. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052934
       - `travaux_accessibilite_residence_principale`: taux 0.25, plafond varies. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052936
       - `interets_emprunt_habitation_ancien`: taux 0.25, for contracts before 2014 reference. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052938
    **IS domain — 3 new files:**

    6. **exonerations.yaml** (values type, unit: currency-EUR): Exonérations d'IS. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053112. Under values.2025-01-01.value:
       - `pme_nouvelle`: exonération sur les premiers 38,120 € de bénéfice
       - `jei` (Jeune Entreprise Innovante): exonération 100% première année, 50% deuxième année
       - `zfu_te` (Zone Franche Urbaine — Territoire Entrepreneur): exonération 100% puis dégressive
       - `zrr` (Zone de Revitalisation Rurale): exonération partielle plafonnée
       - `ber` (Bassin d'Emploi à Redynamiser): exonération dégressive

    7. **report_deficits.yaml** (values type, unit: currency-EUR/ratio): Report des déficits fiscaux. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053114. Under values.2025-01-01.value:
       - `carryback_duree` (1 an, créance de carry-back)
       - `carryforward_duree` (illimitée)
       - `carryforward_plafond_fixe` (1,000,000 € — base intouchable)
       - `carryforward_plafond_pct_excedent` (0.50 — 50% of profit exceeding 1M€)
       - `formule`: "déficit imputable = min(déficit reportable, 1 000 000 + 0.50 × max(0, bénéfice - 1 000 000))"

    8. **CVAE.yaml** (values type, unit: /1): Cotisation sur la Valeur Ajoutée des Entreprises. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053116. Under values.2025-01-01.value:
       - `taux_effectif_2025` (0.0028 — in path to abolition, was 0.0075 before reform)
       - `degrevement_plafond_pct_va` (0.02 — capping at 2% of valeur ajoutée)
       - `chiffre_affaires_minimum` (152,500 €)
       - `degrevement_calcul`: "min(CVAE_brute, CVAE_brute × (plafond - CA) / seuil)"
       - `plafond_ca_2025` (50,000,000 €)
       - `abolition_path`: "0.28% en 2025 → 0.19% en 2026 → 0.09% en 2027 → 0% en 2028"

    **TVA domain — 2 new files:**

    9. **franchise.yaml** (values type, unit: currency-EUR): Franchise en base de TVA. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053130. Under values.2025-01-01.value:
       - `biens_livraisons` (91,900 € seuil, 101,000 € tolérance)
       - `prestations_services` (36,800 € seuil, 39,100 € tolérance)
       - `avocats_auteurs` (47,600 € seuil, 58,600 € tolérance)

    10. **exonerations.yaml** (values type, unit: /1): Exonérations TVA sectorielles. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053132. Under values.2025-01-01.value — each entry is a boolean (applicable or not), list of standard EU exemptions:
        - `medical_paramedical` (true, art. 261 CGI)
        - `enseignement_scolaire_universitaire` (true)
        - `operations_bancaires_financieres` (true)
        - `operations_assurance_reassurance` (true)
        - `services_postaux_universels` (true)
        - `location_logements_nus_usage_habitation` (true)
        - `livraisons_immeubles_plus_5_ans` (true, achevés depuis +5 ans)
        - `organismes_sans_but_lucratif` (true, under conditions)

    **Domain index.yaml updates — 3 files:**
    For `packages/tax-rules/parameters/ir/index.yaml`, `is/index.yaml`, `tva/index.yaml`: add new file entries to the `parameters` list following the existing format (`file: xxx.yaml, description: ...`). Preserve all existing entries.
  </action>
  <verify>
    <automated>cd packages/data-pipeline && python3 -c "
import sys, yaml
from pathlib import Path
base = Path('../tax-rules/parameters')
domains = {
    'ir': ['quotient_familial', 'decote', 'plafonnement_qf', 'cehr'],
    'is': ['exonerations', 'report_deficits', 'CVAE'],
    'tva': ['franchise', 'exonerations'],
}
all_ok = True
for domain, files in domains.items():
    for f in files:
        path = base / domain / f'{f}.yaml'
        try:
            with open(path) as fh:
                data = yaml.safe_load(fh)
            assert 'description' in data, f'{path}: missing description'
            assert 'metadata' in data and 'reference' in data['metadata'], f'{path}: missing metadata.reference'
            if 'values' in data:
                assert '2025-01-01' in data['values'], f'{path}: missing 2025-01-01'
            else:
                assert 'brackets' in data, f'{path}: missing values or brackets'
            print(f'  OK: {path}')
        except Exception as e:
            print(f'  FAIL: {path} — {e}')
            all_ok = False
# Check credits.yaml expanded to 25+
with open(base / 'ir' / 'credits.yaml') as fh:
    credits = yaml.safe_load(fh)
entry_count = len(credits.get('values', {}).get('2025-01-01', {}).get('value', {}))
assert entry_count >= 25, f'credits.yaml has {entry_count} entries, expected ≥25'
print(f'  OK: credits.yaml has {entry_count} entries')
if all_ok:
    print('ALL YAML FILES VALID')
else:
    sys.exit(1)
"</automated>
  </verify>
  <done>
    All 9 new YAML files (IR: 4, IS: 3, TVA: 2) parse via yaml.safe_load() with description, metadata.reference, and 2025-01-01 date keys. credits.yaml contains ≥25 entries with legislation references. Domain index.yaml files reference all files.
  </done>
</task>

<task type="auto">
  <name>Task 2: Expand Cotisations and Aides YAML parameter files</name>
  <files>
    packages/tax-rules/parameters/cotisations/allegements_fillon.yaml
    packages/tax-rules/parameters/cotisations/forfait_social.yaml
    packages/tax-rules/parameters/cotisations/pass.yaml
    packages/tax-rules/parameters/cotisations/index.yaml
    packages/tax-rules/parameters/aides/aah.yaml
    packages/tax-rules/parameters/aides/aspa.yaml
    packages/tax-rules/parameters/aides/css.yaml
    packages/tax-rules/parameters/aides/cheque_energie.yaml
    packages/tax-rules/parameters/aides/allocation_rentree_scolaire.yaml
    packages/tax-rules/parameters/aides/paje.yaml
    packages/tax-rules/parameters/aides/are.yaml
    packages/tax-rules/parameters/aides/index.yaml
  </files>
  <action>
    Create 10 new YAML parameter files and update 2 domain index.yaml files. All follow the same OpenFisca-compatible pattern: `description` → `metadata.reference` (legifrance.gouv.fr) → `values.{2025-01-01}.value` with nested parameters.

    **Cotisations domaine — 3 new files:**

    1. **allegements_fillon.yaml** (values type, unit: /1): Réduction générale des cotisations patronales (ex-réduction Fillon). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053140. Under values.2025-01-01.value:
       - `coefficient_max_t` — 0.4257 (entreprises &lt; 50 salariés) / 0.4284 (≥ 50 salariés)
       - `formule_coefficient`: "(T / 0.6) × (1.6 × SMIC_annuel / rémunération_annuelle - 1)"
       - `smic_annuel_151_67h` (21,621.60 € — SMIC annualisé pour 151.67h/mois 2025)
       - `plafond_remuneration` — 1.6 × SMIC (soit 34,594.56 € annuel)
       - `cas_particuliers`: régime Alsace-Moselle (coefficient modifié), temps partiel (SMIC proratisé)
       - `cumul_autres_exonerations`: réduction calculée après déduction des autres exonérations

    2. **forfait_social.yaml** (values type, unit: /1): Forfait social sur les contributions patronales. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053142. Under values.2025-01-01.value:
       - `taux_normal` (0.20 — 20% base rate)
       - `taux_reduit_epargne_salariale_pme_premier_accord` (0.00 — exonération PME &lt; 50 salariés, premier accord int/participation)
       - `taux_reduit_interessement_pme` (0.08 — 8% pour intéressement dans PME &lt; 250 salariés)
       - `taux_retraite_supplementaire` (0.20)
       - `taux_prevoyance` (0.20)
       - `assiette`: contributions patronales de prévoyance complémentaire, retraite supplémentaire, intéressement, participation, PEE/PERCO

    3. **pass.yaml** (values type, unit: currency-EUR): Plafond Annuel de la Sécurité Sociale. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053144. Under values.2025-01-01.value:
       - `pass_annuel` (47,100 €)
       - `pass_mensuel` (3,925 €)
       - `pass_trimestriel` (11,775 €)
       - `pass_quinzenal` (1,963 €)
       - `pass_hebdomadaire` (906 €)
       - `pass_journalier` (216 €)
       - `usage`: "Plafond de référence pour les cotisations plafonnées (vieillesse, AGIRC-ARRCO T1, prévoyance) et les seuils de nombreuses prestations sociales"

    **Aides domaine — 7 new files:**

    4. **aah.yaml** (values type, unit: currency-EUR): Allocation aux Adultes Handicapés. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053150. Under values.2025-01-01.value:
       - `montant_mensuel_maximal` (1,016.05 € — 2025 rate)
       - `plafond_ressources_celibataire` (11,656 € annuel)
       - `plafond_ressources_couple` (23,312 € annuel)
       - `taux_incapacite_minimum` (0.80 — ≥80% or 50-79% with RSDAE)
       - `abattement_revenus_activite` (varies, like RSA cumul mechanism)
       - `majoration_vie_autonome` (335.30 €/mois supplement if independent living)
       - `cumul_aah_salaire`: dégressive reduction formula

    5. **aspa.yaml** (values type, unit: currency-EUR): Allocation de Solidarité aux Personnes Âgées (minimum vieillesse). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053152. Under values.2025-01-01.value:
       - `montant_mensuel_personne_seule` (1,012.02 €)
       - `montant_mensuel_couple` (1,571.16 €)
       - `plafond_ressources_personne_seule` (12,144.24 € annuel)
       - `plafond_ressources_couple` (18,853.92 € annuel)
       - `age_minimum` (65 ans, sauf inaptitude au travail)
       - `condition_residence`: résidence stable et régulière en France ≥ 6 mois/an
       - `recuperation_succession`: récupérable sur succession si actif net ≥ 39,000 €

    6. **css.yaml** (values type, unit: currency-EUR): Complémentaire Santé Solidaire. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053154. Under values.2025-01-01.value:
       - `css_gratuite_plafond_annuel` (10,166 € — 2025 ceiling for free CSS, 1 personne)
       - `css_participative_plafond_annuel` (13,724 € — ceiling for €1/day CSS)
       - `participation_age_moins_29_ans` (8 €/mois)
       - `participation_age_30_49_ans` (14 €/mois)
       - `participation_age_50_59_ans` (21 €/mois)
       - `participation_age_60_69_ans` (25 €/mois)
       - `participation_age_70_ans_plus` (30 €/mois)
       - `majoration_plafond_par_personne_supplementaire` (+50% par personne)

    7. **cheque_energie.yaml** (values type, unit: currency-EUR): Chèque énergie. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053156. Under values.2025-01-01.value — brackets structure (like bareme.yaml) with `rfr_par_uc_max` as threshold and `montant` as rate:
       - Bracket 1: RFR/UC &lt; 5,700 € → 277 €
       - Bracket 2: RFR/UC 5,700–6,800 € → 202 €
       - Bracket 3: RFR/UC 6,800–7,850 € → 148 €
       - Bracket 4: RFR/UC 7,850–11,000 € → 48 €
       - `unite_consommation_formule`: "1 UC pour 1er adulte + 0.5 UC par adulte suppl. + 0.3 UC par enfant"

    8. **allocation_rentree_scolaire.yaml** (values type, unit: currency-EUR): Allocation de Rentrée Scolaire (ARS). Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053158. Under values.2025-01-01.value:
       - `montant_6_10_ans` (416.40 €)
       - `montant_11_14_ans` (439.38 €)
       - `montant_15_18_ans` (454.60 €)
       - `plafond_rfr_1_enfant` (27,141 € for 1 dependent child)
       - `plafond_rfr_2_enfants`: (27,141 + 6,264) €
       - `plafond_rfr_par_enfant_supplementaire` (+6,264 € per additional child)
       - `condition_age`: enfant 6-18 ans scolarisé / en apprentissage (rémunération ≤ 55% SMIC)

    9. **paje.yaml** (values type, unit: currency-EUR): Prestation d'Accueil du Jeune Enfant. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053160. Under values.2025-01-01.value:
       - `prime_naissance` (1,019.43 € — versée au 7e mois de grossesse)
       - `prime_adoption` (2,038.86 €)
       - `allocation_base_taux_plein` (189.39 €/mois)
       - `allocation_base_taux_partiel` (94.70 €/mois)
       - `plafond_rfr_taux_plein_couple_1_revenu` (33,904 €, enfant né avant 2025)
       - `plafond_rfr_taux_partiel_couple_1_revenu` (45,394 €)
       - `cmg_moins_3_ans_taux_plein` (max 507.67 €/mois, varies by income)
       - `cmg_3_6_ans_taux_plein` (max 253.83 €/mois)
       - `prepare_arret_total` (422.21 €/mois)
       - `prepare_temps_partiel_50pc` (272.83 €/mois)

    10. **are.yaml** (values type, unit: currency-EUR): Allocation d'Aide au Retour à l'Emploi. Reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049053162. Under values.2025-01-01.value:
        - `taux_sjr_minimum` (0.57 — 57% of SJR, higher of two formulas)
        - `taux_sjr_partie_fixe` (0.404 — 40.4% SJR + partie fixe)
        - `partie_fixe_journaliere` (13.30 €/jour)
        - `allocation_minimale_journaliere` (31.59 €)
        - `allocation_plafond_journalier` (289.46 € — 75% SJR cap)
        - `plafond_sjr_mensuel` (15,456 € — 4 × PASS)
        - `duree_indemnisation_formule`: "min(jours_travaillés × 1.0, 730 jours calendaires — moins de 53 ans)"
        - `duree_indemnisation_53_54_ans` (822 jours max avec possibilité prolongation)
        - `duree_indemnisation_55_ans_plus` (1,095 jours max)
        - `delai_carence_conge_paye` (7 jours)
        - `delai_carence_specifique` (varies based on indemnités supra-légales)

    **Domain index.yaml updates — 2 files:**
    Update `packages/tax-rules/parameters/cotisations/index.yaml` and `aides/index.yaml`: add new file entries to `parameters` list following existing format. Preserve all existing entries.
  </action>
  <verify>
    <automated>cd packages/data-pipeline && python3 -c "
import sys, yaml
base = Path('../tax-rules/parameters')
domains = {
    'cotisations': ['allegements_fillon', 'forfait_social', 'pass'],
    'aides': ['aah', 'aspa', 'css', 'cheque_energie', 'allocation_rentree_scolaire', 'paje', 'are'],
}
all_ok = True
for domain, files in domains.items():
    for f in files:
        path = base / domain / f'{f}.yaml'
        try:
            with open(path) as fh:
                data = yaml.safe_load(fh)
            assert 'description' in data, f'{path}: missing description'
            assert 'metadata' in data and 'reference' in data['metadata'], f'{path}: missing metadata.reference'
            if 'values' in data:
                assert '2025-01-01' in data['values'], f'{path}: missing 2025-01-01'
            else:
                assert 'brackets' in data, f'{path}: missing values or brackets'
            print(f'  OK: {path}')
        except Exception as e:
            print(f'  FAIL: {path} — {e}')
            all_ok = False
if all_ok:
    print('ALL AIDES/COTISATIONS YAML FILES VALID')
else:
    sys.exit(1)
"</automated>
  </verify>
  <done>
    All 10 new YAML files (cotisations: 3, aides: 7) parse via yaml.safe_load() with description, metadata.reference, and 2025-01-01 date keys. Domain index.yaml files updated to reference all new files.
  </done>
</task>

<task type="auto">
  <name>Task 3: Expand canonical profiles from 16 to 32 with systematic dimensional coverage</name>
  <files>
    packages/data-pipeline/src/validation/canonical_profiles.py
    packages/data-pipeline/tests/test_validation.py
  </files>
  <action>
    Expand CANONICAL_PROFILES list from 16 to 32 entries in `packages/data-pipeline/src/validation/canonical_profiles.py`. Add 16 new profiles systematically covering all 7 dimensions identified in the 01-UAT.md gap diagnosis. Each profile follows the existing dict schema with `name`, `description`, `situation_familiale`, `nb_enfants`, `revenus` (salaires/pensions/bnc/fonciers), `patrimoine` (immobilier/financier), `zone_residence`, and `expected_results` stubs.

    Insert new profiles after the `haut_revenu` profile (line ~363, before the closing `]`). Add a section comment header `# ── Expanded profiles (gap closure #2: +16 profiles for dimensional coverage) ──`.

    **16 new profiles, organized by dimension:**

    *Income stratification (threshold gaps at CEHR and IR boundaries):*
    17. `fam_monoparentale_1_enfant` — Parent divorcé, 1 enfant (8 ans), 22,000 € salaire, zone2. Description: "Parent isolé avec 1 enfant à charge — configuration monoparentale la plus courante en France, test 1.5 parts QF et allocations". situation_familiale: divorce, nb_enfants: 1, salaires: [22000.0], immobilier: 0.0, financier: 2000.0, zone2.
    18. `celibataire_100k_patrimoine` — Célibataire, 100,000 € salaire, 100,000 € financier, zone1. Description: "Haut revenu célibataire avec patrimoine financier significatif — approche du seuil CEHR célibataire, test CSG sur revenus du patrimoine". situation_familiale: celibataire, nb_enfants: 0, salaires: [100000.0], immobilier: 0.0, financier: 100000.0, zone1.
    19. `celibataire_250k_cehr` — Célibataire, 250,000 € salaire, zone1. Description: "Seuil exact CEHR 3% célibataire — test déclenchement contribution exceptionnelle hauts revenus (D-12)". situation_familiale: celibataire, nb_enfants: 0, salaires: [250000.0], immobilier: 500000.0, financier: 200000.0, zone1.
    20. `couple_1_enfant` — Couple marié, 1 enfant, 45,000 € + 35,000 € salaires, zone2. Description: "Couple bi-actif avec 1 enfant — test 2.5 parts QF, plafonnement QF non déclenché". situation_familiale: marie, nb_enfants: 1, salaires: [45000.0, 35000.0], immobilier: 280000.0, financier: 25000.0, zone2.
    21. `couple_500k_cehr` — Couple marié, 0 enfant, 500,000 € salaire total (250K+250K), zone1. Description: "Seuil exact CEHR 4% couple — test plafonnement QF et taux marginal maximal couple". situation_familiale: marie, nb_enfants: 0, salaires: [250000.0, 250000.0], immobilier: 800000.0, financier: 400000.0, zone1.

    *Zone residence (zone3 coverage at multiple income points):*
    22. `celibataire_smic_zone3` — Célibataire SMIC (18,801 €), zone3. Description: "SMIC en zone détendue — test différentiel APL zone3 vs zone2, taux d'effort logement". situation_familiale: celibataire, nb_enfants: 0, salaires: [18801.0], immobilier: 0.0, financier: 0.0, zone3.
    23. `retraite_modeste_zone3` — Retraité célibataire, pension 15,000 €, propriétaire 120,000 €, zone3. Description: "Petite retraite en zone3 — test ASPA éligibilité, taxe foncière modeste, exonération TH". situation_familiale: celibataire, nb_enfants: 0, pensions: [15000.0], immobilier: 120000.0, financier: 8000.0, zone3.
    24. `independant_bic_zone3` — Indépendant BIC, 35,000 € bénéfice, zone3. Description: "Commerçant en zone rurale — test cotisations minimales, différentiel CFE zone3, micro-BIC". situation_familiale: celibataire, nb_enfants: 0, bic: 35000.0, immobilier: 80000.0, financier: 15000.0, zone3.

    *Asset profiles (IFI/big wealth, pure financial wealth):*
    25. `rentier_foncier` — Couple marié, 1 enfant, salaire 70,000 € + revenus fonciers 50,000 € (3 biens), zone1. Description: "Gros patrimoine immobilier locatif — test IFI, revenus fonciers au réel, déficit foncier imputation". situation_familiale: marie, nb_enfants: 1, salaires: [70000.0], fonciers: [25000.0, 15000.0, 10000.0], immobilier: 1500000.0, financier: 150000.0, zone1.
    26. `jeune_patrimoine_financier` — Célibataire, 50,000 € salaire, 200,000 € financier, pas d'immo, zone1. Description: "Jeune cadre avec patrimoine financier uniquement — test flat tax (30% PFU), prélèvements sociaux sur revenus du capital". situation_familiale: celibataire, nb_enfants: 0, salaires: [50000.0], immobilier: 0.0, financier: 200000.0, zone1.

    *Profession types (agricole, micro-entrepreneur):*
    27. `agriculteur_zone3` — Célibataire, 28,000 € bénéfice agricole, zone3. Description: "Exploitant agricole — test régime BA (bénéfice agricole), cotisations MSA, moyenne triennale". situation_familiale: celibataire, nb_enfants: 0, salaires: [], bnc: [], fonciers: [], bic: 28000.0, immobilier: 180000.0 (exploitation), financier: 12000.0, zone3. For the `revenus` dict, use `benefice_agricole: [28000.0]` as a custom key (extend the existing structure consistently).
    28. `auto_entrepreneur` — Célibataire, 25,000 € CA micro-entrepreneur, zone2. Description: "Micro-entrepreneur — test versement libératoire IR, micro-social, chiffre d'affaires vs bénéfice". situation_familiale: celibataire, nb_enfants: 0, revenus with `micro_bic: 25000.0` and `versement_liberatoire: true`, immobilier: 0.0, financier: 5000.0, zone2.

    *Social benefit edge cases:*
    29. `handicape_aah` — Célibataire, AAH 12,192 €/an (1,016€×12), incapacité ≥80%, zone2. Description: "Bénéficiaire AAH à taux plein — test allocation adulte handicapé, couverture santé solidaire, exonération taxe habitation". situation_familiale: celibataire, nb_enfants: 0, salaires: [0.0], pensions: [0.0], allocations_chomage: 0.0, aa_h: 12192.0 (note: extend revenus dict with `aa_h` key), immobilier: 0.0, financier: 1000.0, zone2.
    30. `senior_aspa` — Veuf·ve >65 ans, ASPA minimum vieillesse (12,144 €/an), zone3. Description: "Bénéficiaire ASPA seul — test minimum vieillesse, couverture maladie universelle, récupération sur succession potentielle". situation_familiale: veuf, nb_enfants: 0, pensions: [5000.0], immobilier: 80000.0 (résidence principale), financier: 3000.0, zone3. Add note: ASPA = complément différentiel (total ressources porté à 12,144 €).
    31. `jeune_precaire` — Célibataire 25 ans, 10,000 € salaire intermittent + 8,000 € ARE, zone2. Description: "Jeune en emploi partiel + chômage — test cumul salaire-ARE, prime d'activité jeunes, RSA jeune actif (< 25 ans, condition d'activité)". situation_familiale: celibataire, nb_enfants: 0, salaires: [10000.0], allocations_chomage: 8000.0, immobilier: 0.0, financier: 500.0, zone2.

    *Cross-category combinations:*
    32. `retraite_proprietaire_modeste` — Couple retraité, pension combinée 30,000 €, résidence 200,000 € + financier 30,000 €, zone2. Description: "Couple retraité propriétaire modeste — test croisé retraite × patrimoine, décote IR, exonération taxe foncière (âge)". situation_familiale: marie, nb_enfants: 0, pensions: [18000.0, 12000.0], immobilier: 200000.0, financier: 30000.0, zone2.
    33. `independant_famille_3enfants` — Indépendant BNC marié, 3 enfants (3, 8, 14 ans), 45,000 € bénéfice, zone3. Description: "Croisé indépendant × famille nombreuse en zone détendue — test cumul allocations familiales, ARS, Paje, crédits d'impôt garde + scolarité, et cotisations minimales". situation_familiale: marie, nb_enfants: 3, bnc: [45000.0], immobilier: 220000.0, financier: 20000.0, zone3.

    After adding all 16 profiles, the list MUST contain exactly 32 entries.

    **Update test_validation.py:**
    In `packages/data-pipeline/tests/test_validation.py`, edit `test_profile_count_at_least_fourteen`:
    1. Rename method to `test_profile_count_at_least_thirty` (reflecting new lower bound)
    2. Change assertion from `assert count >= 14` to `assert count >= 30`
    3. Update docstring: "At least 30 profiles defined (expanded from 14 per gap closure UAT #2)."
    4. Update the f-string assertion message to say `≥30` instead of `≥14`
    The test in `test_export_creates_file_with_required_keys` on line 174 also has `>= 14` — update to `>= 30`.
  </action>
  <verify>
    <automated>cd packages/data-pipeline && python3 -c "
from validation.canonical_profiles import CANONICAL_PROFILES
count = len(CANONICAL_PROFILES)
assert count == 32, f'Expected 32 canonical profiles, got {count}'
# Verify all required fields
required = ['name', 'description', 'situation_familiale', 'revenus', 'patrimoine', 'zone_residence']
names = []
for p in CANONICAL_PROFILES:
    for f in required:
        assert f in p, f'{p.get(\"name\",\"?\")} missing field {f}'
    names.append(p['name'])
# Unique names
assert len(names) == len(set(names)), f'Duplicate names: {names}'
# Verify 7 dimensions coverage
text = ' '.join(p['description'] for p in CANONICAL_PROFILES)
# Income: SMIC, 100K, 250K, 500K thresholds present
profiles_at_thresholds = [n for n in names if 'smic' in n or '250k' in n or '500k' in n or '100k' in n]
assert len(profiles_at_thresholds) >= 4, f'Threshold coverage missing: found {profiles_at_thresholds}'
# Zone3: at least 5 profiles
zone3 = [p for p in CANONICAL_PROFILES if p['zone_residence'] == 'zone3']
assert len(zone3) >= 5, f'Zone3 profiles: {len(zone3)}, expected ≥5'
# Family structures: monoparentale_1_enfant, couple_1_enfant, famille_nombreuse
assert any('monoparentale' in n and '1' in n for n in names), 'Missing single parent +1 child'
assert any('couple_1_enfant' == n for n in names), 'Missing couple_1_enfant'
# Profession types: agriculteur, auto_entrepreneur
assert any('agriculteur' in n for n in names), 'Missing agriculteur profile'
assert any('auto_entrepreneur' in n for n in names), 'Missing auto_entrepreneur'
# Social benefit: aah, aspa, jeune_precaire
assert any('handicape' in n for n in names), 'Missing AAH profile'
assert any('senior_aspa' == n for n in names), 'Missing ASPA profile'
# Cross-category: retraite+proprietaire, independant+famille
assert any('retraite' in n and 'proprietaire' in n for n in names), 'Missing retiree x owner'
assert any('independant' in n and 'famille' in n for n in names), 'Missing independant x famille'
print(f'ALL 32 PROFILES VALID — {count} total, {len(zone3)} zone3, dimensions covered')
" && python3 -c "
# Verify test threshold gating
import ast, sys
with open('tests/test_validation.py') as f:
    code = f.read()
# Check method renamed or threshold updated
has_30 = '>= 30' in code
has_thirty = 'thirty' in code.lower()
if not has_30:
    print('FAIL: test still uses >= 14 threshold')
    sys.exit(1)
print('OK: test threshold updated to ≥30')
"</automated>
  </verify>
  <done>
    32 canonical profiles in CANONICAL_PROFILES with all required fields and unique names. All 7 dimensions covered with at least 2 profiles per dimension. test_profile_count_at_least_thirty uses ≥30 threshold and passes.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| YAML author input → yaml.safe_load() | Malformed YAML or invalid parameter values enter the pipeline |
| YAML data → JSON Schema validator | Structural violations (missing required fields) must be caught before JSON output |
| credits.yaml entries → downstream consumers | Incorrect tax credit rates/plafonds produce wrong simulation results |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-05 | Tampering | New YAML parameter files | mitigate | JSON Schema Draft 2020-12 validation gate (parameter.schema.json) catches any missing `description`, non-string `metadata.reference`, missing `2025-01-01` date key, or malformed brackets structure. ALL new files pass through the existing yaml2json/validate.py pipeline before CI accepts them. |
| T-01-06 | Information Disclosure | All new YAML files | accept | No PII in YAML files — only fiscal parameter values with public legislation references. Same disposition as T-01-04 from Plan 01. |
| T-01-07 | Tampering | credits.yaml expansion | mitigate | Expanded credits.yaml uses same legifrance.gouv.fr reference URLs as existing entries. Negative test: deliberately remove `reference` from one entry and confirm schema validation rejects it. |
| T-01-08 | Denial of Service | canonical_profiles.py | accept | 32 profiles × ~20 lines each = ~640 lines. Python module import cost is negligible (< 10ms). No risk of memory exhaustion or import timeouts. |
| T-01-09 | Tampering | test_validation.py threshold | mitigate | Threshold update from ≥14 to ≥30 is source-controlled and reviewed. CI gate (`pytest tests/test_validation.py`) enforces the new threshold on every push. |
</threat_model>

<verification>
**Phase-level verification (runs after all tasks):**

1. **YAML parse check:** `python3 -c "import yaml; from pathlib import Path; [yaml.safe_load(open(f)) for f in Path('packages/tax-rules/parameters').rglob('*.yaml') if f.name != 'index.yaml']"` — zero parse errors across all data files.

2. **JSON conversion gate:** Run the existing yaml2json pipeline: `python3 packages/data-pipeline/src/yaml2json/convert.py`. All parameter files (original 12 + new 18 = 30+) must convert without schema validation errors.

3. **Index integrity:** For each domain, every `.yaml` file (except index.yaml) must appear in its domain's `index.yaml` parameters list. Verify: `python3 -c "..."` checking file-to-index coverage.

4. **Canonical profile count:** `python3 -c "from validation.canonical_profiles import CANONICAL_PROFILES; assert len(CANONICAL_PROFILES) == 32"` passes.

5. **Test suite:** `pytest tests/test_validation.py -v` passes on all profile integrity tests with updated ≥30 threshold.

6. **CI compatibility:** No CI workflow file modifications needed — existing `phase1-validate.yml` schema-validation and conversion-test jobs will pick up new YAML files automatically.
</verification>

<success_criteria>
- [ ] 18 new YAML parameter files created across all 5 domains (IR: 4, IS: 3, TVA: 2, cotisations: 3, aides: 7 — excluding credits.yaml which is an expansion, not new file)
- [ ] credits.yaml expanded from 3 to ≥25 entries with legislation references
- [ ] 5 domain index.yaml files updated to reference all new parameter files
- [ ] All YAML files parse via yaml.safe_load() without errors
- [ ] YAML→JSON conversion pipeline produces valid JSON for all parameter files (zero schema validation rejections)
- [ ] CANONICAL_PROFILES contains exactly 32 profiles with unique names and all required fields
- [ ] Canonical profiles cover all 7 UAT-identified dimensions with at least 2 profiles per dimension
- [ ] test_validation.py test_profile_count assertion updated to ≥30
- [ ] All existing tests continue to pass with expanded data
- [ ] UAT test #1 (YAML Tax Rules Parse Correctly) now passes — 30+ files with full domain coverage
- [ ] UAT test #6 (Canonical Profiles Cover Edge Cases) now passes — 32 profiles with systematic coverage
</success_criteria>

<output>
After completion, create `.planning/phases/01-data-foundation-rules-engine/01-GAP-CLOSURE-SUMMARY.md`
</output>
