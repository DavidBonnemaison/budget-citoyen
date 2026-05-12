# Codegen Spike Results

Generated: 2026-05-12T18:49:02.433312+00:00

## Overview

- **Total variables:** 2777
- **Formula-bearing:** 937

## Spike Variables

| Variable | Entity | Domain | Auto-gen? | Blockers |
|----------|--------|--------|-----------|----------|
| rni | foyer_fiscal | ir | ✓ | — |
| ir_brut | foyer_fiscal | ir | ✓ | — |
| decote | foyer_fiscal | ir | ✓ | — |
| rsa | famille | other | ✓ | — |
| apl | famille | other | ✓ | — |
| aide_logement_montant | famille | aides | ✓ | — |
| revenu_disponible | menage | other | ✓ | — |
| csg | individu | other | ✓ | — |

## Summary

- Spiked: 8
- Auto-generatable: 8 (100.0%)
- Manual: 0

## Broad Scan (937 formulas)

- Auto: 815 (87.0%)
- Manual: 122

### Top Blockers
- numpy where() call: 92
- numpy astype() call: 30

## Detailed Analysis

### rni

- Entity: foyer_fiscal | Domain: ir | Period: 0001-01-01
- Deps: abat_spe, rng
- Auto-gen: Yes

**Python:**
```python
def formula(foyer_fiscal, period, parameters):
        rng = foyer_fiscal('rng', period)
        abat_spe = foyer_fiscal('abat_spe', period)

        return rng - abat_spe
```

**Rust preview:**
```rust
    let rng = calculate_rng(parameters, period, profile);
    let abat_spe = calculate_abat_spe(parameters, period, profile);

    return rng - abat_spe;
```

### ir_brut

- Entity: foyer_fiscal | Domain: ir | Period: 0001-01-01
- Deps: nbptr, rni, taux_effectif
- Auto-gen: Yes

**Python:**
```python
def formula(foyer_fiscal, period, parameters):
        nbptr = foyer_fiscal('nbptr', period)
        taux_effectif = foyer_fiscal('taux_effectif', period)
        rni = foyer_fiscal('rni', period)
        bareme = parameters(period).impot_revenu.bareme_ir_depuis_1945.bareme

        return (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni
```

**Rust preview:**
```rust
    let nbptr = calculate_nbptr(parameters, period, profile);
    let taux_effectif = calculate_taux_effectif(parameters, period, profile);
    let rni = calculate_rni(parameters, period, profile);
    let bareme = parameters.get_brackets("impot_revenu/bareme_ir_depuis_1945/bareme").unwrap_or_default();

    return if (taux_effectif) == (0) { nbptr } else { 0.0_f64 } * bareme.calc(rni / nbptr) + taux_effectif * rni;
```

### decote

- Entity: foyer_fiscal | Domain: ir | Period: 2014-01-01
- Deps: ir_plaf_qf, nb_adult
- Auto-gen: Yes

**Python:**
```python
def formula_2014_01_01(foyer_fiscal, period, parameters):
        ir_plaf_qf = foyer_fiscal('ir_plaf_qf', period)
        nb_adult = foyer_fiscal('nb_adult', period)
        taux_decote = parameters(period).impot_revenu.calcul_impot_revenu.plaf_qf.decote.taux
        decote_seuil_celib = parameters(period).impot_revenu.calcul_impot_revenu.plaf_qf.decote.seuil_celib
        decote_seuil_couple = parameters(period).impot_revenu.calcul_impot_revenu.plaf_qf.decote.seuil_couple
        decote_celib = max_(0, decote_seuil_celib - taux_decote * ir_plaf_qf)
        decote_couple = max_(0, decote_seuil_couple - taux_decote * ir_plaf_qf)

        return around((nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple)
```

**Rust preview:**
```rust
    let ir_plaf_qf = calculate_ir_plaf_qf(parameters, period, profile);
    let nb_adult = calculate_nb_adult(parameters, period, profile);
    let taux_decote = parameters.get_scalar("impot_revenu/calcul_impot_revenu/plaf_qf/decote/taux").unwrap_or(0.0);
    let decote_seuil_celib = parameters.get_scalar("impot_revenu/calcul_impot_revenu/plaf_qf/decote/seuil_celib").unwrap_or(0.0);
    let decote_seuil_couple = parameters.get_scalar("impot_revenu/calcul_impot_revenu/plaf_qf/decote/seuil_couple"
```

### rsa

- Entity: famille | Domain: other | Period: 2009-06-01
- Deps: rsa_montant, rsa_non_calculable
- Auto-gen: Yes

**Python:**
```python
def formula_2009_06(famille, period):
        montant = famille('rsa_montant', period)
        non_calculable = famille('rsa_non_calculable', period)

        return (non_calculable == TypesRSANonCalculable.calculable) * montant
```

**Rust preview:**
```rust
    let montant = calculate_rsa_montant(parameters, period, profile);
    let non_calculable = calculate_rsa_non_calculable(parameters, period, profile);

    return (non_calculable == 1.0_f64) * montant;
```

### apl

- Entity: famille | Domain: other | Period: 0001-01-01
- Deps: aide_logement_montant, logement_conventionne
- Auto-gen: Yes

**Python:**
```python
def formula(famille, period):
        aide_logement_montant = famille('aide_logement_montant', period)
        logement_conventionne = famille.demandeur.menage('logement_conventionne', period)

        return aide_logement_montant * logement_conventionne
```

**Rust preview:**
```rust
    let aide_logement_montant = calculate_aide_logement_montant(parameters, period, profile);
    let logement_conventionne = famille.demandeur.calculate_logement_conventionne(parameters, period, profile);

    return aide_logement_montant * logement_conventionne;
```

### aide_logement_montant

- Entity: famille | Domain: aides | Period: 0001-01-01
- Deps: aide_logement_montant_brut_crds, crds_logement
- Auto-gen: Yes

**Python:**
```python
def formula(famille, period):
        aide_logement_montant_brut = famille('aide_logement_montant_brut_crds', period)
        crds_logement = famille('crds_logement', period)
        montant = round_(aide_logement_montant_brut + crds_logement, 2)

        return montant
```

**Rust preview:**
```rust
    let aide_logement_montant_brut = calculate_aide_logement_montant_brut_crds(parameters, period, profile);
    let crds_logement = calculate_crds_logement(parameters, period, profile);
    let montant = ((aide_logement_montant_brut + crds_logement) * 100.0_f64).round() / 100.0_f64;

    return montant;
```

### revenu_disponible

- Entity: menage | Domain: other | Period: 0001-01-01
- Deps: impots_directs, pensions_nettes, ppe, prestations_sociales, revenus_nets_du_capital, revenus_nets_du_travail
- Auto-gen: Yes

**Python:**
```python
def formula(menage, period, parameters):
        pensions_nettes_i = menage.members('pensions_nettes', period)
        revenus_nets_du_capital_i = menage.members('revenus_nets_du_capital', period)
        revenus_nets_du_travail_i = menage.members('revenus_nets_du_travail', period)
        pensions_nettes = menage.sum(pensions_nettes_i)
        revenus_nets_du_capital = menage.sum(revenus_nets_du_capital_i)
        revenus_nets_du_travail = menage.sum(revenus_nets_du_travail_i)

        impots_directs = menage('impots_directs', period)

        # On prend en compte les PPE touchés par un foyer fiscal dont le déclarant principal est dans le ménage
        ppe_i = menage.members.foyer_fiscal('ppe', period)  # PPE du foyer fiscal auquel appartient chaque membre du ménage
        ppe = menage.sum(ppe_i, role = FoyerFiscal.DECLARANT_PRINCIPAL)  # On somme seulement pour les déclarants principaux

        # On prend en compte les prestations sociales touchées par une famille dont le demandeur est dans le ménage
        prestations_sociales_i = menage.members.famille('prestations_sociales', period)  # PF de la famille auquel appartient chaque membre du ménage
        prestations_sociales = menage.sum(prestations_sociales_i, role = Famille.DEMANDEUR)  # On somme seulement pour les demandeurs

        return (
            revenus_nets_du_travail
            + impots_directs
            + pensions_nettes
            + ppe
            + prestations_sociales
            + revenus_nets_du_capital
            )
```

**Rust preview:**
```rust
    let pensions_nettes_i = calculate_pensions_nettes(parameters, period, profile);
    let revenus_nets_du_capital_i = calculate_revenus_nets_du_capital(parameters, period, profile);
    let revenus_nets_du_travail_i = calculate_revenus_nets_du_travail(parameters, period, profile);
    let pensions_nettes = pensions_nettes_i;
    let revenus_nets_du_capital = revenus_nets_du_capital_i;
    let revenus_nets_du_travail = revenus_nets_du_travail_i;

    let impots_directs = calculate_impots_direct
```

### csg

- Entity: individu | Domain: other | Period: 0001-01-01
- Deps: csg_deductible_chomage, csg_deductible_non_salarie, csg_deductible_retraite, csg_deductible_salaire, csg_glo_assimile_salaire_ir_et_ps, csg_imposable_chomage, csg_imposable_non_salarie, csg_imposable_retraite, csg_imposable_salaire, csg_revenus_capital
- Auto-gen: Yes

**Python:**
```python
def formula(individu, period):
        csg_imposable_salaire = individu('csg_imposable_salaire', period, options = [ADD])
        csg_deductible_salaire = individu('csg_deductible_salaire', period, options = [ADD])
        csg_imposable_chomage = individu('csg_imposable_chomage', period, options = [ADD])
        csg_deductible_chomage = individu('csg_deductible_chomage', period, options = [ADD])
        csg_imposable_retraite = individu('csg_imposable_retraite', period, options = [ADD])
        csg_deductible_retraite = individu('csg_deductible_retraite', period, options = [ADD])
        csg_imposable_non_salarie = individu('csg_imposable_non_salarie', period, options = [ADD])
        csg_deductible_non_salarie = individu('csg_deductible_non_salarie', period, options = [ADD])
        csg_glo_assimile_salaire_ir_et_ps = individu('csg_glo_assimile_salaire_ir_et_ps', period)
        # CSG sur revenus du capital, définie à l'échelle du foyer fiscal, mais projetée sur le déclarant principal
        csg_revenus_capital = individu.foyer_fiscal('csg_revenus_capital', period)
        csg_revenus_capital_projetee = csg_revenus_capital * individu.has_role(FoyerFiscal.DECLARANT_PRINCIPAL)

        return (
            csg_imposable_salaire
            + csg_deductible_salaire
            + csg_imposable_chomage
            + csg_deductible_chomage
            + csg_imposable_retraite
            + csg_deductible_retraite
            + csg_imposable_non_salarie
            + csg_deductible_non_salarie
            + csg_glo_assimile_salaire_ir_et_ps
            + csg_revenus_capital_projetee
            )
```

**Rust preview:**
```rust
    let csg_imposable_salaire = calculate_csg_imposable_salaire(parameters, period, profile);
    let csg_deductible_salaire = calculate_csg_deductible_salaire(parameters, period, profile);
    let csg_imposable_chomage = calculate_csg_imposable_chomage(parameters, period, profile);
    let csg_deductible_chomage = calculate_csg_deductible_chomage(parameters, period, profile);
    let csg_imposable_retraite = calculate_csg_imposable_retraite(parameters, period, profile);
    let csg_deductible_r
```

## Conclusions

- 87.0% auto-generatable — simple arithmetic, brackets, parameter access translate well
- Main blockers: cross-entity navigation, role-based aggregation, OpenFisca enum types
- Estimated auto-generated LOC: ~{bs['formulas_analyzed'] * 20} (avg 20 lines × {bs['formulas_analyzed']} formulas)
