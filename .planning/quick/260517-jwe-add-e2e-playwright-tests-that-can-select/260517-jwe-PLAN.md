---
phase: quick
plan: 260517-jwe
type: execute
wave: 1
depends_on: []
files_modified:
  - webapp/src/__tests__/interaction.spec.ts
  - webapp/package.json
autonomous: true
requirements: []

must_haves:
  truths:
    - "User can run `npm run test:e2e:headed` and see the browser GUI on their laptop"
    - "Tests select scenario cards by clicking them, and verify impact display appears"
    - "Tests move slider thumbs via keyboard (ArrowRight/ArrowLeft) and verify output values change"
    - "Tests cover the full workflow: preselect → select scenario → move sliders → réinitialiser"
  artifacts:
    - path: "webapp/src/__tests__/interaction.spec.ts"
      provides: "Comprehensive Playwright e2e tests for scenario selection and slider manipulation"
      min_lines: 120
    - path: "webapp/package.json"
      provides: "New test:e2e:headed script"
      contains: "test:e2e:headed"
  key_links:
    - from: "package.json test:e2e:headed"
      to: "playwright CLI --headed flag"
      via: "npm run"
    - from: "interaction.spec.ts"
      to: "http://localhost:5173"
      via: "Playwright config baseURL"
    - from: "interaction.spec.ts scenario tests"
      to: "ScenarioCard buttons with aria-pressed"
      via: "page.locator('button[aria-pressed]').click()"
    - from: "interaction.spec.ts slider tests"
      to: "LeverSlider role='slider' + keyboard events"
      via: "page.getByRole('slider').focus() + page.keyboard.press('ArrowRight')"
---

<objective>
Add comprehensive Playwright e2e tests for scenario selection and slider interaction, plus a headed-mode
script so the user can watch tests run in a visible browser on their laptop.

Purpose: The existing `simulator.spec.ts` covers basic flow but lacks dedicated tests for the full
          scenario→sliders→impact verification workflow. Adding a `--headed` option lets the user
          visually debug test behavior on their local machine (macOS).

Output:
  - `webapp/src/__tests__/interaction.spec.ts` — new spec file with 10+ focused tests
  - `webapp/package.json` — new `test:e2e:headed` script entry
</objective>

<execution_context>
@/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/user/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@webapp/playwright.config.ts
@webapp/src/__tests__/simulator.spec.ts    (existing patterns)
@webapp/src/components/ScenarioCard.tsx     (button with aria-pressed)
@webapp/src/components/ScenarioGrid.tsx     (grid layout, h2 "Choisissez un scénario pour commencer")
@webapp/src/components/LeverSlider.tsx      (React Aria slider, role="slider", output element)
@webapp/src/components/SliderGroup.tsx      (5 levers: ir, is, tva, cotisations, depenses)
@webapp/src/state/index-map.ts             (LEVER_MAPPINGS with lever names)
@webapp/src/engine/types.ts                (ScenarioDefinition, ScenarioResult)
@webapp/src/pages/SimulatorPage.tsx         (layout: left panel scenarios+sliders, right panel impact+charts)
@webapp/src/hooks/useSimulation.ts          (state machine: loading→preselect→displaying)

<interfaces>
<!-- Key DOM contracts the executor references in locators. Extracted from source. -->

ScenarioCard (button):
  - Locator: `button[aria-pressed]`
  - Selected state: `ring-2 ring-primary` CSS classes
  - aria-label: `"Sélectionner le scénario {name}"`
  - Text content: scenario.name (h3) + scenario.description (p)

LeverSlider (React Aria useSlider):
  - Locator: `page.getByRole('slider')` → returns slider thumb divs
  - Group role: `role="group"` with `aria-label={label}`
  - Label text: `"Variation ({mapping.name})"` — e.g. "Variation (IR ménages)"
  - Output element: `<output>` showing formatted value + " %"
  - Value attribute: `value` on the slider role element (e.g. "0", "5", "-3")
  - Range: min=-15, max=15, step=1
  - Hidden native input for touch screen readers

SliderGroup:
  - Section with aria-label="Curseurs budgétaires"
  - 5 levers in order: ir, is, tva, cotisations, depenses
  - Section headers: "IR ménages", "IS entreprises", "TVA", "Cotisations sociales", "Dépenses publiques"
  - Réinitialiser button: `page.getByRole('button', { name: 'Réinitialiser' })`

ImpactDisplay:
  - Text: "Impact sur votre foyer" visible after scenario selection
  - Text: "Foyer modeste" (one of the profile labels)

Playwright config:
  - baseURL: http://localhost:5173
  - testDir: ./src/__tests__, testMatch: **/*.spec.ts
  - webServer auto-starts `npx vite --port 5173`
  - Projects: chromium, firefox, webkit, mobile-chrome, mobile-safari
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add test:e2e:headed script to package.json</name>
  <files>webapp/package.json</files>
  <action>
Add a `"test:e2e:headed"` script entry inside the `"scripts"` block of `webapp/package.json`.
The script should run: `playwright test --headed`

Place it immediately after the existing `"test:e2e": "playwright test"` line so scripts are grouped logically.

The `--headed` flag is a built-in Playwright CLI option that disables headless mode and shows the
browser GUI — no additional configuration needed. When combined with the existing playwright.config.ts
webServer auto-start, `npm run test:e2e:headed` will:
  1. Start the Vite dev server on port 5173 (if not already running)
  2. Open visible Chromium/Firefox/WebKit browsers
  3. Execute all spec files in src/__tests__/

Do NOT add a separate `test:e2e:debug` script — `--headed` is sufficient for visual debugging.
Do NOT modify the existing `test:e2e` script.
  </action>
  <verify>
    <automated>cd webapp && node -e "const pkg = require('./package.json'); const scripts = pkg.scripts; console.assert(scripts['test:e2e:headed'] === 'playwright test --headed', 'missing or wrong script'); console.log('OK: test:e2e:headed =', scripts['test:e2e:headed'])"</automated>
  </verify>
  <done>`npm run test:e2e:headed` invokes Playwright with `--headed` flag, opening visible browsers</done>
</task>

<task type="auto">
  <name>Task 2: Create interaction.spec.ts with scenario selection + slider manipulation tests</name>
  <files>webapp/src/__tests__/interaction.spec.ts</files>
  <action>
Create `webapp/src/__tests__/interaction.spec.ts` with comprehensive Playwright e2e tests.

**File structure:** Follow the existing pattern from `simulator.spec.ts` (import from `@playwright/test`, use `test.describe` blocks with descriptive French names, `test()` functions with `async ({ page })`).

**Test groups to implement:**

1. **`test.describe('Scenario Selection')`** — 3 tests:
   - `test('clicking a scenario card selects it and shows impact display')` — go to `/`, wait for cards visible, click first card, verify `page.getByText('Impact sur votre foyer')` is visible, verify `page.getByText('Projections macroéconomiques')` is visible, verify the clicked card has CSS class `ring-primary` (selected state)
   - `test('selecting a different scenario deselects the previous one')` — go to `/`, click first card, click second card (nth=1), verify first card does NOT have `ring-primary`, verify second card has `ring-primary`
   - `test('keyboard Enter/Space activates a focused scenario card')` — go to `/`, focus first card with Tab, press Space, verify Impact display appears

2. **`test.describe('Slider Keyboard Interaction')`** — 4 tests:
   - `test('all 5 sliders are present and enabled after scenario selection')` — go to `/`, wait for auto-init (the app auto-selects baseline on init, so sliders should appear after loading), wait for `page.getByRole('slider').first()` to be enabled. Then verify `page.getByRole('slider')` count is at least 5 (plus hidden inputs — use `page.locator('[role="slider"]')` count for thumb divs specifically; React Aria sliders have one thumb div with `role="slider"` each). Verify each is enabled.
   - `test('ArrowRight increments slider value')` — go to `/`, wait for auto-init/displaying state, get first slider, read initial value attribute, focus it, press ArrowRight, verify new value > initial value (or not equal for edge case at max)
   - `test('ArrowLeft decrements slider value')` — same pattern, press ArrowLeft, verify value decreased
   - `test('slider output label updates after keyboard adjustment')` — go to `/`, wait for displaying, get first slider's containing group (`page.getByRole('group').first()`), read the `<output>` text content, focus the slider, press ArrowRight 3 times, verify the `<output>` text content has changed

3. **`test.describe('Slider Mouse Interaction')`** — 2 tests:
   - `test('clicking on slider track moves thumb')` — go to `/`, wait for displaying. Get first slider's track area (the div containing the thumb, which is the direct child of the group's track area). Click at position {x: 75%, y: center} on the track (approximates setting higher value). Verify slider's `value` attribute changed from its initial value.
   - `test('mouse drag on slider thumb adjusts value continuously')` — This is best-effort with React Aria. Use `page.mouse` to simulate drag: move to thumb position, mouse down, move right, mouse up. Verify value changed. NOTE: If React Aria's pointer event handling proves brittle in Playwright, fall back to asserting keyboard interaction as the primary interaction test and mark mouse-drag as optional/skipped with a comment explaining React Aria's synthetic event model.

4. **`test.describe('Full Workflow')`** — 3 tests:
   - `test('complete flow: select scenario → adjust sliders → réinitialiser')` — go to `/`, wait for displaying state (auto-init), note the selected scenario name, adjust 2 different sliders (ir + tva) via ArrowRight x3 each, verify impact display still visible, click Réinitialiser button (`page.getByRole('button', { name: 'Réinitialiser' }).first()`), verify preselect screen is back (heading "Choisissez un scénario pour commencer" visible)
   - `test('adjusting all 5 sliders updates the URL state parameter')` — go to `/`, wait for displaying, adjust each slider (ArrowRight once each, tab between), wait 500ms for URL debounce, verify `page.url()` contains `state=`
   - `test('slider values persist visible state after rapid consecutive adjustments')` — go to `/`, wait for displaying, focus first slider, press ArrowRight 5 times rapidly, verify the output value settled and the page didn't crash (no error overlay — check `Impact sur votre foyer` still visible)

**Locator strategy (important for reliability):**
- Scenario cards: `page.locator('button[aria-pressed]')` — these are the pressable toggle buttons
- Selected card check: `page.locator('button[aria-pressed].ring-primary')` or `page.locator('button[aria-pressed="true"]')`
- Sliders: `page.getByRole('slider')` — React Aria applies `role="slider"` to the thumb div
- Slider group containers: `page.getByRole('group')` — each slider is wrapped in a `role="group"` with `aria-label` matching the lever label
- Impact display: `page.getByText('Impact sur votre foyer')`
- Preselect heading: `page.getByRole('heading', { name: 'Choisissez un scénario pour' })` or `page.getByText('Choisissez un scénario pour commencer')`
- Réinitialiser: `page.getByRole('button', { name: 'Réinitialiser' }).first()` (desktop and mobile both render this button)

**Timeout strategy:** Use generous timeouts (10000-30000ms) for initial load waits since the app loads WASM/Web Workers on first visit. For interactions after the app is loaded, default Playwright timeouts (5000ms) are fine.

**Auto-init awareness:** The app auto-selects the baseline scenario on init (see `useSimulation.ts` lines 172-201). This means after `page.goto('/')`, the app transitions through `loading → displaying` without user clicking a card. Tests should `await expect(page.getByText('Impact sur votre foyer')).toBeVisible({ timeout: 30000 })` to wait for this transition. Most slider tests can operate on the auto-selected baseline without explicitly clicking a card first.

Do NOT duplicate tests already in `simulator.spec.ts` (e.g., splash screen transition, URL state content, methodology page visit, loading indicator pulse). Focus on scenario selection fidelity and slider manipulation mechanics.
  </action>
  <verify>
    <automated>cd webapp && npx playwright test --grep "Scenario Selection|Slider Keyboard|Slider Mouse|Full Workflow" --project=chromium 2>&1 | tail -30</automated>
  </verify>
  <done>
All playwright tests pass across chromium project:
  - Scenario cards are clickable and show impact display
  - Selected state (aria-pressed, CSS ring) updates correctly when switching cards
  - All 5 sliders are visible and enabled after init
  - Keyboard ArrowRight/ArrowLeft changes slider value and output label
  - Clicking slider track changes slider value
  - Réinitialiser returns to preselect state
  - URL updates after slider adjustments
  - No test flakiness (tests pass consistently in headed and headless mode)
  </done>
</task>

</tasks>

<verification>
After both tasks complete:
1. Run `cd webapp && npm run test:e2e:headed -- --project=chromium` — observe Chromium open visibly, tests execute, browser closes
2. Run `cd webapp && npm run test:e2e -- --project=chromium` — all tests pass headless (CI-safe)
3. Verify the new `interaction.spec.ts` tests appear in the Playwright HTML report
</verification>

<success_criteria>
- `npm run test:e2e:headed` opens a visible browser and runs all e2e tests (new + existing)
- `interaction.spec.ts` has at least 12 tests across 4 describe blocks
- All tests pass in both headed and headless mode
- No regression: existing `simulator.spec.ts` and `a11y.spec.ts` tests still pass
</success_criteria>

<output>
After completion, create `.planning/quick/260517-jwe-add-e2e-playwright-tests-that-can-select/260517-jwe-SUMMARY.md`
</output>
