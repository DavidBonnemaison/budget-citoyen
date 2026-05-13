# Phase 3: Interactive Simulation Shell (MVP) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Phase:** 03-interactive-simulation-shell-mvp
**Areas discussed:** Simulation UX Model, Slider Organization, Chart Architecture, General UI, Loading & Empty States

---

## Simulation UX Model

| Option | Description | Selected |
|--------|-------------|----------|
| Scenario selector + macro sliders | Preserve Phase 2 architecture: citizens pick pre-computed scenarios, macro sliders only interactive. Phase 2 compliant. | |
| Scenario selector + micro interpolation | Add interpolation between pre-computed scenarios for micro results. Continuous slider feel with approximate accuracy. | ✓ |
| Partial live micro engine | Build simplified TS micro calculator for live slider response. More accurate but reopens Phase 2 scope. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Aggregate tax rate axis | Single lever interpolates between scenarios on a global tax rate axis. | |
| Per-tax interpolation | Each tax slider interpolates independently between nearest scenarios. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| 4-6 scenarios | Baseline + 3-5 political programs. Limited coverage. | |
| 9-12 scenarios | Baseline + programs + variants. Better interpolation accuracy. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Confidence labels | "Estimation" / "Valeur exacte" badges. | |
| Ranges | Display as range (e.g. "+50€ à +80€/mois"). | |
| Just show the result | Single number + footnote "Basé sur les scénarios les plus proches." | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Independent macro axes | Macro sliders always freely adjustable, scenario only sets micro. | |
| Scenario-synced | Scenario selection auto-sets macro slider positions. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Single median-income profile | One "foyer type" at median French income. | |
| 3 representative profiles | Bas revenu (SMIC), médian (26K€), aisé (60K€). | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Scenario first, sliders second | Select scenario → see results → adjust sliders. | ✓ |
| Sliders first, scenario as preset | Sliders primary, scenario as preset button. | |

---

## Slider Organization

| Option | Description | Selected |
|--------|-------------|----------|
| 4-5 simplified levers | Grouped aggregates: IR, IS, TVA, Cotisations, Dépenses. | ✓ |
| Full 14 parameters | All index-map.ts params visible. | |
| 2 macro sliders only | Tax + spend only, no micro levers. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Collapsible sections | Expandable groups with progressive disclosure. | ✓ |
| Tabbed groups | One tax category visible at a time. | |
| Single scrollable list | All sliders in one vertical list. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Percentage change from baseline | Slider centered at 0%, shows ±X%. | ✓ |
| Absolute rate values | Actual tax rate values on slider. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Abstract levers + advanced toggle | Default: 5 grouped levers. Toggle reveals individual params. | ✓ |
| Abstract levers only | No drill-down available. | |
| Individual levers only | Always show all 14 params. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Weighted proportional mapping | Each lever drives multiple params in fixed proportions. | ✓ |
| Single representative param | Each lever controls one param, others stay at baseline. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Notch + "Actuel" label | Visual notch at 0% with label. | ✓ |
| Color-coded fill | Red left / green right of baseline. | |
| No indicator | Clean, minimal slider. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Reset all to baseline | Returns all sliders to 0%, deselects scenario. | ✓ |
| Reset to selected scenario | Returns sliders to current scenario's values. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Throttled drag + instant release | ~50ms throttle during drag, full compute on release. | ✓ |
| Release-only computation | Only compute when user releases slider. | |

---

## Chart Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| D3.js 7.9 | Full SVG DOM control for ARIA. STACK.md primary choice. | |
| Vega-Lite 6.4 | Declarative specs, built-in aria-label. | ✓ |
| D3 + Vega-Lite hybrid | D3 for simulation charts, Vega-Lite for methodology page. | |

| Option | Description | Selected |
|--------|-------------|----------|
| 2x2 grid | Four small multiples in responsive grid. | ✓ |
| Stacked vertically | 4 full-width charts scrolling. | |
| Single combined chart with toggles | One chart, series toggle buttons. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Line charts with area fill | Lines + semi-transparent fill. Insee/OECD convention. | ✓ |
| Bar charts | Grouped bars per year. | |
| Sparklines | Compact inline charts. | |

| Option | Description | Selected |
|--------|-------------|----------|
| SVG post-process + HTML table | Post-process SVG to inject patterns, add sibling HTML table. | |
| Color-only high-contrast palette | Deuteranopia-safe colors, no patterns. | |
| Vega marks with custom SVG pattern encoding | Encode patterns within Vega-Lite declarative spec. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Hover tooltips + legend highlighting | Hover shows value, legend hover highlights series. | ✓ |
| Static charts | No interaction. | |
| Hover tooltips only | Lightweight, no highlighting. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Greyed chart + warning message | Grey overlay with "Paramètres hors domaine de validité." | ✓ |
| Hide chart, show message only | Replace chart with message. | |
| Clamp to nearest boundary | Silently return nearest valid result. | |

---

## General UI

| Option | Description | Selected |
|--------|-------------|----------|
| Single scrollable page | Sections stacked vertically. | |
| Split panel layout | Left: scenario + sliders. Right: impact + charts. | ✓ |
| Tabbed view | Tabs for each section. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Base64-encoded query param | Single `?state=<base64>` param. | ✓ |
| Plain query params | Individual `?ir=+15&is=+5...` params. | |
| Hash fragment | State in `#` fragment. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stack vertically + accordion panels | Mobile: panels stack, each section collapsible. | ✓ |
| Bottom sheet for sliders | Sliders slide up from bottom on mobile. | |
| Tab switching on mobile | Tabs toggle between settings and results. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated page /methodologie | Separate page linked from footer. | ✓ |
| Collapsible footer section | Methodology at bottom of main page. | |
| Modal overlay | Button opens modal with attribution info. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Niveau collège (Brevet) | 14-15 ans, no technical terms. | |
| Niveau lycée | 16-18 ans, some terms with tooltips. | ✓ |
| Langage journalistique | Le Monde / France Info level. | |

---

## Loading & Empty States

| Option | Description | Selected |
|--------|-------------|----------|
| Branded splash with progress | Logo + loading text + progress indicator. | ✓ |
| Skeleton screen | Immediate page structure with animated placeholders. | |
| Blank with spinner | Centered spinner only. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Scenarios grid with prompt | Show all scenarios, prompt to choose, charts show placeholder. | ✓ |
| Auto-select baseline | Automatically select Baseline 2025 on load. | |
| Guided tour overlay | First-visit overlay highlighting sections. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Subtle pulse on affected charts | Opacity pulse on chart areas during computation. | ✓ |
| Global spinner in corner | Small spinner in top-right during any computation. | |
| No indicator | Results update fast enough, no explicit indicator. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Error screen with retry | Full-screen error + "Réessayer" button. | ✓ |
| Degraded mode | Show available features, hide failed ones. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Cache-first for data, network-first for shell | Scenario JSON + shock matrix cached, app shell network-first. | ✓ |
| Cache everything aggressively | All assets cached with long TTL. | |
| No Service Worker for v1 | Defer SW to Phase 5. | |

---

## the agent's Discretion

- Exact interpolation algorithm (inverse distance weighting recommended)
- Lever-to-parameter mapping proportions
- Slider range values (±X%)
- Tailwind CSS theme and palette
- Vega-Lite spec structure and encoding
- HTML table fallback format for screen readers
- Service Worker implementation details
- Splash screen progress indicator design
- React Aria component configuration
- Route structure (React Router vs conditional rendering)
- axe-core CI pipeline integration

## Deferred Ideas

None — discussion stayed within Phase 3 scope.
