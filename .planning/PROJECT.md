# Budget Citoyen

## What This Is

Un simulateur budgétaire hybride et interactif permettant au grand public et aux équipes de campagne d'évaluer l'impact socio-fiscal et macroéconomique des réformes politiques. La plateforme combine un moteur microéconomique côté client (compilé en WebAssembly pour une exécution locale et privée) avec un moteur macroéconomique pré-calculé (matrice des chocs dérivée du modèle Mésange de l'Insee/Trésor) pour offrir des résultats instantanés sans transfert de données personnelles.

## Core Value

Permettre à tout citoyen de comprendre en temps réel l'impact budgétaire et macroéconomique d'une réforme fiscale sur son foyer et sur l'économie nationale, sans vocabulaire comptable complexe et sans jamais transmettre ses données personnelles.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Simulateur microéconomique : calcul de l'impact des réformes fiscales sur des profils types (IR, IS, TVA, cotisations, aides sociales)
- [ ] Moteur macroéconomique : projection des trajectoires de déficit, emploi, croissance et dette via la matrice des chocs
- [ ] Interface interactive avec curseurs budgétaires (temps de réponse < 200ms)
- [ ] Visualisations des résultats (graphiques, tableaux de bord) avec accessibilité RGAA 4
- [ ] Moteur Rules as Code en JSON/YAML pour la logique législative auditable
- [ ] Données synthétiques (50 000 profils) respectant le RGPD via confidentialité différentielle
- [ ] Architecture Privacy by Design : zéro transfert de données personnelles client→serveur
- [ ] Mode expert pour analystes/chercheurs avec API REST et exports (CSV, JSON)
- [ ] Profils multiples : Citoyen Explorateur (vulgarisé), Expert Politique/Médias (avancé)

### Out of Scope

- Comptes utilisateurs et hébergement de données personnelles — toute l'expérience reste locale via le cache WASM du navigateur
- Variations dynamiques des taux d'intérêt — le coût de refinancement utilise des taux lissés constants

## Context

- Projet développé pour les échéances électorales de 2027 en France
- S'appuie sur l'écosystème open-source de microsimulation : OpenFisca (Python, AGPL) et PolicyEngine (policyengine-core)
- Utilise le modèle macroéconomique Mésange (Insee/Direction Générale du Trésor) comme référence
- Le code fiscal sera compilé en WebAssembly depuis Rust (via wasm-pack, wasm-bindgen) pour exécution côté navigateur
- Conformité RGAA 4 obligatoire pour l'accessibilité (service public)
- Conformité RGPD/CNIL via données synthétiques générées par IA (copules, GAN, VAE) avec confidentialité différentielle

## Constraints

- **Performance** : Latence < 200ms pour l'actualisation des graphiques lors de la manipulation des curseurs
- **Sécurité** : Aucune donnée personnelle ne quitte le poste client (Privacy by Design)
- **Accessibilité** : Conformité RGAA 4 (critères 1.1, 1.3, thématiques 3, 8, 11)
- **Tech stack** : Moteur micro en Rust/WASM, interface web, données en JSON/YAML
- **Licence** : Open source (compatible AGPL d'OpenFisca)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Moteur micro en WASM (Rust) plutôt que Python serveur | Performance locale, Privacy by Design, zéro coût infra de calcul | — Pending |
| Matrice des chocs pré-calculée plutôt que résolution en temps réel | Modèle Mésange trop lourd pour le temps réel ; interpolation multi-linéaire garantit < 200ms | — Pending |
| Données synthétiques plutôt que données fiscales réelles | Conformité RGPD/CNIL, impossibilité légale d'utiliser les registres administratifs | — Pending |
| Fork/adaptation d'OpenFisca ou PolicyEngine pour le moteur de règles | Écosystème mature, Rules as Code, auditable par des non-programmeurs | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-11 after initialization*
