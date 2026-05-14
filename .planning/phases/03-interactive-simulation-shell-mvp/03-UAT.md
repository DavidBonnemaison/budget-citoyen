---
status: complete
phase: 03-interactive-simulation-shell-mvp
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md, 03-08-SUMMARY.md
started: 2026-05-14T09:15:00Z
updated: 2026-05-14T14:25:00Z
---

## Current Test

[testing complete]

## Tests

### 1. App Loads with Splash Screen
expected: Navigate to http://localhost:5173. The app shows a branded "Budget Citoyen" splash screen with a progress bar and loading phase text. After loading completes, it transitions to the scenario selection view.
result: pass

### 2. Scenario Selection Grid
expected: After loading, the app shows a grid of scenario cards. Each card shows a scenario name and description. The grid is responsive (1 column on narrow, 2 on tablet, 3 on desktop).
result: issue
reported: "it works, but too much text on each card for a 3 columns layout on desktop, the descrption is too truncated. Also, there's no visual cue that the cards are clickable (no border, no elevation, ...) ... Titles overflow from cards, and still too clamped. Use a 2 columns layout on desktop too ... Maybe it's the aside of 380px in desktop that is too small, it's too cramped even with only two columns"
severity: cosmetic

### 3. Select a Scenario Card
expected: Click a scenario card. The card shows a visual selection ring (ring-2). After selection, the app transitions to the simulator view with sliders and impact display.
result: pass

### 4. Slider Drag Interaction
expected: Drag the IR (Impôt sur le revenu) slider thumb. The value updates in real-time with French percent formatting (e.g., "+5 %" or "−3 %"). The slider has a gradient track and a baseline "Actuel" notch at the zero position.
result: pass

### 5. Collapsible Slider Sections and Reset
expected: Five collapsible lever sections are shown. The IR section is expanded by default. Clicking a section header expands/collapses it. The "Réinitialiser" button resets all sliders to their baseline positions.
result: pass

### 6. Advanced Mode Toggle
expected: Click the "Mode avancé" toggle. It shows an "Actif" badge when enabled and "Inactif" when disabled. When active, sub-parameter sliders appear within each lever section.
result: pass

### 7. Impact Display Pills
expected: After adjusting a slider, the impact section shows 3 household profile pills (e.g., "Foyer modeste", "Foyer médian", "Foyer aisé") with €/mois values. Green indicates gain, red indicates loss, and a dash shows for null/unavailable values.
result: pass

### 8. Chart Grid with SVG Patterns
expected: A 2×2 grid of charts (Déficit public, Dette publique, Croissance du PIB, Emploi) is displayed. Charts render as SVG with distinct pattern fills (diagonal lines, dots, crosshatch, vertical stripes) rather than relying solely on color.
result: pass

### 9. Methodology Page
expected: Click the "Méthodologie et sources" link in the footer. The page navigates to /methodologie showing static methodology content. The footer is persistent across pages.
result: pass

### 10. Mobile Responsive Layout
expected: Resize the browser to a narrow viewport (~375px). The layout switches to a single-column/accordion mode. Slider controls and impact/charts stack vertically instead of the desktop split-panel layout.
result: pass

## Summary

total: 10
passed: 9
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Navigate to http://localhost:5173. The app shows a branded 'Budget Citoyen' splash screen with a progress bar and loading phase text. After loading completes, it transitions to the scenario selection view."
  status: resolved
  reason: "User reported: the splash screen with a progress bar and loading phase text appears, but the scenario selection never appears"
  severity: major
  test: 1
  root_cause: "Two issues: (1) useSimulation.init() never called — no useEffect triggers it. (2) shock-matrix-v2025.1.bin file missing from public/data/ — Vite SPA fallback returns index.html, worker parses HTML as binary → Float64Array error."
  artifacts:
    - path: "webapp/src/hooks/useSimulation.ts"
      issue: "init() function is never invoked — missing useEffect"
    - path: "webapp/public/data/"
      issue: "shock-matrix-v2025.1.bin does not exist"
    - path: "webapp/src/engine/macro-interpolate.ts"
      issue: "Empty Float64Arrays from zero-dim matrix crash findInterval() — missing guard"
  missing:
    - "Add useEffect(() => { init(); }, [init]); inside useSimulation to auto-trigger init on mount"
    - "Generate minimal shock-matrix-v2025.1.bin placeholder (16 bytes, all-zero dimensions)"
    - "Add empty-array guards to macro-interpolate.ts for placeholder matrix safety"

- truth: "After loading, the app shows a grid of scenario cards. Each card shows a scenario name and description. The grid is responsive."
  status: failed
  reason: "User reported: cards lacked clickable visual cues, descriptions too truncated at 3-col, titles overflowed, 380px panel too cramped for cards"
  severity: cosmetic
  test: 2
  root_cause: "380px panel too narrow for card layout — applied 2-col grid, border/shadow, overflow-hidden but panel remains cramped"
  artifacts:
    - path: "webapp/src/components/ScenarioCard.tsx"
      issue: "Missing border/shadow on unselected cards, overflow on titles"
    - path: "webapp/src/components/ScenarioGrid.tsx"
      issue: "3-col grid too cramped in 380px panel"
  missing:
    - "Consider wider left panel or single-column card layout for preselect phase"
  debug_session: ""
