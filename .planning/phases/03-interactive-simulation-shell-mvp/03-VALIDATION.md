---
phase: 3
slug: interactive-simulation-shell-mvp
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.6 (unit/integration) + Playwright 1.60.0 (E2E/a11y) |
| **Config file** | `vitest.config.ts` + `playwright.config.ts` (new — Wave 0) |
| **Quick run command** | `npx vitest run src/state/__tests__/url-codec.test.ts` |
| **Full suite command** | `npx vitest run && npx playwright test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npx vitest run src/state/__tests__/` (unit tests for codec/interpolation/index-map)
- **After every plan wave:** Run `npx vitest run && npx playwright test tests/a11y.spec.ts` (unit + accessibility)
- **Before `/gsd-verify-work`:** Full suite must be green (`npx vitest run && npx playwright test`)
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-{plan}-01 | TBD | TBD | UI-01 | T-03-01 / Input val | Slider values range-checked (min/max), finite check, type coercion | e2e | `npx playwright test tests/a11y.spec.ts:sliders` | ❌ W0 | ⬜ pending |
| 03-{plan}-02 | TBD | TBD | UI-02 | — | Interpolation returns valid ScenarioResult with source attribution | unit + e2e | `npx vitest run src/state/__tests__/interpolation.test.ts` | ❌ W0 | ⬜ pending |
| 03-{plan}-03 | TBD | TBD | UI-03 | T-03-02 / Vega-Lite spec injection | Charts rendered via pre-defined specs, no user-injectable content | e2e | `npx playwright test tests/simulator.spec.ts:chart-render` | ❌ W0 | ⬜ pending |
| 03-{plan}-04 | TBD | TBD | UI-04 | — | Reset button clears sliders to 0%, deselects scenario | e2e | `npx playwright test tests/simulator.spec.ts:reset` | ❌ W0 | ⬜ pending |
| 03-{plan}-05 | TBD | TBD | UI-05 | T-03-03 / URL state injection | decodeState validates JSON structure, type-checks, ignores unknown fields | unit + e2e | `npx vitest run src/state/__tests__/url-codec.test.ts` | ❌ W0 | ⬜ pending |
| 03-{plan}-06 | TBD | TBD | UI-06 | — | Touch targets ≥ 44px, no horizontal overflow at device widths | e2e | `npx playwright test tests/simulator.spec.ts:mobile --viewport='iPhone 13'` | ❌ W0 | ⬜ pending |
| 03-{plan}-07 | TBD | TBD | UI-07 | — | CSS opacity pulse visible during worker computation, resolves when data arrives | e2e | `npx playwright test tests/simulator.spec.ts:loading` | ❌ W0 | ⬜ pending |
| 03-{plan}-08 | TBD | TBD | UI-08 | — | /methodologie route renders with data source attribution (Insee, budget.gouv.fr, Mésange) | e2e | `npx playwright test tests/simulator.spec.ts:methodology` | ❌ W0 | ⬜ pending |
| 03-{plan}-09 | TBD | TBD | A11Y-01 | — | SVG charts have role="img", aria-labelledby pointing to visible figcaption | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:charts` | ❌ W0 | ⬜ pending |
| 03-{plan}-10 | TBD | TBD | A11Y-02 | — | Adjacent HTML table with `<th scope>` markup exists for each chart | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:tables` | ❌ W0 | ⬜ pending |
| 03-{plan}-11 | TBD | TBD | A11Y-03 | — | SVG pattern fills present in chart SVG, deuteranopia-safe color palette used | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:patterns` | ❌ W0 | ⬜ pending |
| 03-{plan}-12 | TBD | TBD | A11Y-04 | — | No animation exceeds 5s (opacity pulse is 300ms CSS transition) | manual | N/A — well under 5s threshold, verified by code review | N/A | ⬜ pending |
| 03-{plan}-13 | TBD | TBD | A11Y-05 | — | Sliders have aria-valuenow/min/max, keyboard nav (Arrow, Home, End), debounced aria-valuetext on drag-end | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:sliders` | ❌ W0 | ⬜ pending |
| 03-{plan}-14 | TBD | TBD | A11Y-06 | — | axe-core Playwright assertions return no violations | ci-gate | `npx playwright test tests/a11y.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `vitest.config.ts` — Vitest configuration (new)
- [ ] `playwright.config.ts` — Playwright configuration (new)
- [ ] `src/state/__tests__/url-codec.test.ts` — URL state codec unit tests
- [ ] `src/state/__tests__/interpolation.test.ts` — Interpolation algorithm tests
- [ ] `src/state/__tests__/index-map.test.ts` — Lever-to-parameter mapping tests
- [ ] `tests/simulator.spec.ts` — E2E user flow tests
- [ ] `tests/a11y.spec.ts` — Accessibility audit tests (axe-core)
- [ ] Framework install: `npm install -D vitest @playwright/test jsdom @axe-core/playwright`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No animation exceeds 5 seconds (A11Y-04) | A11Y-04 | Opacity pulse is 300ms CSS transition — well under threshold. Verified by code review, no automated timing test needed | Verify CSS transition durations in component source; confirm no animation/transition duration exceeds 5s |
| Niveau lycée reading level (D-26) | D-26 | Cannot be automated reliably — requires human evaluation of citizen-facing French text | Review all copy strings in components; verify short sentences, active voice, "vous"/"votre" address |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
