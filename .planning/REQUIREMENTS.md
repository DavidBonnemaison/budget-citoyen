# Requirements: Budget Citoyen

**Defined:** 2026-05-11
**Core Value:** Permettre à tout citoyen de comprendre en temps réel l'impact budgétaire et macroéconomique d'une réforme fiscale sur son foyer et sur l'économie nationale, sans vocabulaire comptable complexe et sans jamais transmettre ses données personnelles.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Foundation & Rules as Code

- [x] **DATA-01**: Les paramètres fiscaux (IR, IS, TVA, cotisations, aides sociales) sont encodés en YAML sous forme de Rules as Code, convertibles en JSON pour le moteur WASM
- [x] **DATA-02**: Le jeu de données synthétiques (50 000 profils) est généré avec préservation des dépendances entre variables (âge ↔ patrimoine ↔ revenus)
- [x] **DATA-03**: La confidentialité différentielle (ε ≤ 1,0) est implémentée dans le pipeline de génération de données synthétiques
- [x] **DATA-04**: La matrice des chocs macroéconomiques (dérivée du modèle Mésange) est pré-calculée et stockée en look-up table compressée

### Microsimulation Engine

- [ ] **MICRO-01**: Le moteur de microsimulation calcule l'impôt sur le revenu (IR) pour un profil type, exécuté en WASM dans le navigateur
- [ ] **MICRO-02**: Le moteur couvre les variables fiscales majeures : TVA, impôt sur les sociétés (IS), cotisations sociales
- [ ] **MICRO-03**: Le moteur calcule les aides sociales de l'État (prestations, allocations) pour un profil type
- [ ] **MICRO-04**: Le calcul microéconomique s'exécute intégralement côté client sans transfert de données personnelles vers le serveur
- [ ] **MICRO-05**: Le temps de réponse du moteur micro est inférieur à 200ms pour un calcul sur profil type

### Macroeconomic Engine

- [ ] **MACRO-01**: L'interpolation multi-linéaire estime la trajectoire du déficit public à partir de la matrice des chocs et des curseurs utilisateur
- [ ] **MACRO-02**: L'interpolation estime la trajectoire de la dette souveraine
- [ ] **MACRO-03**: L'interpolation estime les projections de croissance (PIB) et d'emploi
- [ ] **MACRO-04**: Les résultats macroéconomiques s'affichent en moins de 200ms après modification d'un curseur
- [ ] **MACRO-05**: Les taux d'intérêt utilisés sont des taux lissés constants (pas de variation en temps réel avec les marchés)

### Interface & Visualisation (Mode Citoyen)

- [ ] **UI-01**: L'utilisateur peut ajuster les principaux leviers fiscaux via des curseurs interactifs (IR, IS, TVA, cotisations)
- [ ] **UI-02**: L'impact sur le pouvoir d'achat d'un foyer type s'affiche en temps réel lors de l'ajustement des curseurs
- [ ] **UI-03**: L'impact sur le déficit public et la dette s'affiche sous forme de graphiques de trajectoire (projection 5 ans)
- [ ] **UI-04**: L'utilisateur peut réinitialiser la simulation à l'état initial
- [ ] **UI-05**: L'utilisateur peut partager sa simulation via une URL encodant l'état complet des paramètres
- [ ] **UI-06**: La plateforme est responsive et fonctionnelle sur mobile (points de touche ≥ 44px)
- [ ] **UI-07**: Un indicateur de chargement est affiché pendant les calculs asynchrones
- [ ] **UI-08**: Les sources de données (Insee, budget.gouv.fr, modèle Mésange) sont attribuées et la méthodologie est documentée

### Accessibilité RGAA 4

- [ ] **A11Y-01**: Les graphiques SVG incluent role="img" et aria-labelledby avec description textuelle
- [ ] **A11Y-02**: Les graphiques Canvas sont accompagnés d'un tableau HTML adjacent avec balises <th scope> appropriées
- [ ] **A11Y-03**: Les séries de données se distinguent par motifs, formes de marqueurs et repères textuels — jamais par la couleur seule
- [ ] **A11Y-04**: Les animations > 5 secondes incluent un mécanisme d'interruption ou d'affichage statique
- [ ] **A11Y-05**: Les curseurs implémentent les attributs WAI-ARIA (aria-valuenow, aria-valuemin, aria-valuemax) et sont navigables au clavier
- [ ] **A11Y-06**: Les audits automatisés d'accessibilité (axe-core) sont intégrés à la CI

### Mode Expert & Analyste

- [ ] **EXP-01**: Le mode expert permet d'empiler plusieurs réformes et d'observer leurs trajectoires macroéconomiques combinées
- [ ] **EXP-02**: L'interface du mode expert expose des paramètres avancés (effectifs de l'État, taux de remplacement)
- [ ] **EXP-03**: Une API REST expose les calculs de simulation, l'impact distributionnel par décile et les exports structurés (CSV, JSON)
- [ ] **EXP-04**: L'arbre de calcul ("show my calculation") est visible pour auditer la logique législative appliquée

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Features

- **NARR-01**: Génération de résumé narratif en langage clair de l'impact d'une réforme (IA client-side ou templates)
- **COMP-01**: Outil de comparaison de programmes électoraux côte à côte avec trajectoires macro
- **CIRCO-01**: Analyse à granularité circonscription législative (intégration Shapefile/GeoPackage, carroyage Insee)
- **GEO-01**: Export GeoPackage pour données territoriales

## Out of Scope

| Feature | Reason |
|---------|--------|
| Comptes utilisateurs et sauvegarde de données personnelles | Violation de l'architecture Privacy by Design, hors périmètre explicite du PRD |
| Variations temps réel des taux d'intérêt (OAT) | Complexité inutile, taux lissés constants suffisants pour la simulation budgétaire |
| Chatbot IA pour conseil fiscal | Territoire réglementé du conseil fiscal, risque juridique |
| Gamification et scores budgétaires | Trivialise les choix fiscaux, nuit à la crédibilité institutionnelle |
| Simulation collaborative temps réel | Complexité WebSocket disproportionnée pour v1, URL de partage suffisant |
| Blockchain pour audit | Complexité inutile, transparence assurée par l'open source et la documentation méthodologique |

---

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| MICRO-01 | Phase 2 | Pending |
| MICRO-02 | Phase 2 | Pending |
| MICRO-03 | Phase 2 | Pending |
| MICRO-04 | Phase 2 | Pending |
| MICRO-05 | Phase 2 | Pending |
| MACRO-01 | Phase 2 | Pending |
| MACRO-02 | Phase 2 | Pending |
| MACRO-03 | Phase 2 | Pending |
| MACRO-04 | Phase 2 | Pending |
| MACRO-05 | Phase 2 | Pending |
| UI-01 | Phase 3 | Pending |
| UI-02 | Phase 3 | Pending |
| UI-03 | Phase 3 | Pending |
| UI-04 | Phase 3 | Pending |
| UI-05 | Phase 3 | Pending |
| UI-06 | Phase 3 | Pending |
| UI-07 | Phase 3 | Pending |
| UI-08 | Phase 3 | Pending |
| A11Y-01 | Phase 3 | Pending |
| A11Y-02 | Phase 3 | Pending |
| A11Y-03 | Phase 3 | Pending |
| A11Y-04 | Phase 3 | Pending |
| A11Y-05 | Phase 3 | Pending |
| A11Y-06 | Phase 3 | Pending |
| EXP-01 | Phase 4 | Pending |
| EXP-02 | Phase 4 | Pending |
| EXP-03 | Phase 5 | Pending |
| EXP-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 32 total
- Mapped to phases: 32
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-11*
*Last updated: 2026-05-11 after roadmap creation (traceability corrected)*
