# Pitfalls Research: Simulateur Budgétaire Citoyen

**Domain:** Civic budget simulation (microsimulation WASM + macro look-up tables + synthetic population + accessible dashboards + client-side privacy)
**Researched:** 2026-05-11
**Confidence:** HIGH (multiple authoritative sources across all domains)

---

## Critical Pitfalls

### Pitfall 1: WASM Serialization Tax Dominates Compute Budget

**What goes wrong:**
The engine compiles to WASM successfully and produces correct results, but crossing the JS↔WASM boundary on every parameter change incurs 5-15ms serialization overhead per call. With 12+ sliders updating at 60fps, total latency breaks the 200ms budget before any actual computation happens.

**Why it happens:**
`wasm-bindgen` serializes/deserializes every value crossing the bridge. When the Rust side receives a structured reform object (JSON-equivalent tree of parameters), each string, float, and nested object crosses individually. Developers prototype with single-call benchmarks (one reform → one result) and miss the cumulative effect of rapid-fire slider interactions. Python-to-WASM translation also introduces subtle overhead from idiomatic Python patterns (dicts, dynamic dispatch) that don't map cleanly to Rust's ownership model.

**How to avoid:**
- Design the WASM boundary as a **batch interface**, not a per-parameter interface. Receive the full reform vector as a single `&[f64]` slice (no serialization) or a flatbuffer.
- Pre-allocate a mutable `SimulationState` struct in WASM linear memory; update individual slider values directly via `UnsafeCell` or index-based setters rather than re-creating the state.
- Benchmark boundary-crossing cost separately from computation cost. Profile with `web_sys::console::time()` / `console.timeEnd()`.
- Consider using `wasm-bindgen`'s `JsValue` only for structured results at the end, not for every input.

**Warning signs:**
- Profiling shows >10ms in JS (not WASM) between slider `input` event and render.
- Each slider update creates a new Rust-side `Simulation` from scratch.
- Console logs show repeated serialization/deserialization per frame.

**Phase to address:**
Phase 1 (Microsimulation Engine — WASM integration). Benchmark boundary crossing during initial PoC before building the full UI.

---

### Pitfall 2: Extrapolation Beyond Pre-Computed Grid — Silent Wrong Answers

**What goes wrong:**
Users set slider combinations (e.g., IS rate = 5% while TVA = 30%) that fall outside the hyper-rectangle of the pre-computed look-up table. The multi-linear interpolation silently extrapolates, producing results that appear plausible (no error, no NaN) but are mathematically invalid — sometimes predicting negative unemployment or GDP growth >50%.

**Why it happens:**
Multi-linear interpolation is well-defined only *within* the convex hull of grid points. Outside this region, it extends the local linear approximation along each axis, producing fantasy values with no macroeconometric basis. Developers assume interpolation = safe, but interpolation ≠ extrapolation. The Mésange model has implicit constraints (e.g., IS + TVA can't simultaneously be extreme) that the look-up table does not enforce.

**How to avoid:**
- **Clamp or clamp-and-warn.** Clamp slider ranges to the grid's defined domain. If a user combination exceeds bounds, display a non-blocking warning: "Ce scénario dépasse le domaine validé du modèle — résultats indicatifs uniquement."
- **Compute the convex hull** of all pre-computed grid points at build time. At runtime, check whether the requested point lies inside the hull via barycentric coordinates or linear programming before evaluating.
- Pre-compute "safe bounds" metadata alongside the matrix — store `min_valid`/`max_valid` per dimension and validate before interpolation.
- For pathological inputs, return `Option<f64>` (Rust-side) and display "non modélisable" in the UI rather than a fake number.

**Warning signs:**
- No bounds-checking code in the interpolation module.
- Slider ranges defined by UI convenience rather than model domain.
- Users can set IS = 0% and TVA = 100% simultaneously.

**Phase to address:**
Phase 3 (Macro Integration — interpolation engine). Bounds validation must be a core deliverable, not an afterthought.

---

### Pitfall 3: Differential Privacy Budget Exhaustion

**What goes wrong:**
The synthetic dataset is generated with a declared ε=1.0 differential privacy guarantee, and the project touts "certified privacy protection." But the 50,000-profile dataset is queried hundreds of times (per decile, per reform variant, per demographic slice) — each query consuming a fraction of the privacy budget. By the time users explore 10 reform scenarios across 8 demographic groups, the effective ε exceeds 100, rendering the DP guarantee meaningless.

**Why it happens:**
Differential privacy uses a **sequential composition** model: if you query the data `t` times with ε-budget per query, the total privacy loss is `t × ε`. Parallel composition only applies when queries operate on *disjoint* subsets. Most dashboard scenarios slice the same data multiple overlapping ways (by age, then by income, then by region), which compounds under sequential composition. Teams focus on the *generation* ε (training the GAN/copula) but forget about *consumption* ε (queries on the deployed dataset). The CNIL specifically warns that synthetic data does not magically become anonymous without accounting for query patterns.

**How to avoid:**
- **Pre-compute all public statistics** (decile tables, Gini coefficients, aggregates by age/region) during the data pipeline phase, applying DP noise once at generation time. The dashboard queries **pre-noised aggregates**, not raw synthetic microdata.
- If raw profiles must be queried interactively, implement a **privacy budget tracker** (Rust-side WASM, since data is local) that refuses queries after ε budget is consumed. Display remaining budget in expert mode.
- Use **zero-Concentrated Differential Privacy (zCDP)** or **Rényi DP** for tighter composition bounds than pure ε-DP.
- Document the total ε consumption across all dashboard views in a published privacy statement. CNIL auditability requires transparency about *how* privacy is maintained, not just that DP was used.
- For synthetic data generation, use DP-SGD (Differentially Private Stochastic Gradient Descent) during training, not post-hoc noise injection. Post-hoc noise on top of a non-DP generator does not compose correctly.

**Warning signs:**
- "DP guarantee" is mentioned but ε value and composition analysis are absent.
- The dashboard issues distinct queries to synthetic profiles per user interaction.
- No privacy budget tracker exists in the system.
- The synthetic data generator doesn't use DP-SGD or DP training.

**Phase to address:**
Phase 2 (Synthetic Population — DP generation pipeline). Privacy budget architecture must be designed before data generation, not retrofitted. This is a CNIL red line.

---

### Pitfall 4: Canvas-Only Charts That Are Invisible to Screen Readers

**What goes wrong:**
The team builds beautiful D3.js/Chart.js data visualizations rendered entirely on `<canvas>`. They pass visual QA perfectly. But screen reader users (JAWS, NVDA, VoiceOver) encounter a black hole — no accessible name, no data table fallback, no keyboard-navigable elements. This fails RGAA 4 criteria 1.1, 1.3, and threatens legal compliance for a public service.

**Why it happens:**
Canvas is a pixel buffer with no DOM structure. Accessibility requires explicit alternative representations. Chart.js, Recharts, and similar libraries default to canvas output and treat accessibility as an opt-in plugin. Teams assume "we'll add alt text later" — but alt text for a multi-series time-series chart (debt trajectory + GDP growth + employment rate, per year, under 3 reform scenarios) is not one string. It needs to be a structured data table. The RGAA explicitly requires that canvas-based charts are paired with an adjacent or toggleable HTML data table. "Image alt text" is insufficient for complex data.

**How to avoid:**
- **SVG-first rendering** with proper ARIA roles (`role="img"`, `aria-labelledby`, `aria-describedby`) for all charts. SVG elements are DOM nodes and individually targetable.
- For every canvas chart, **generate a sibling HTML `<table>`** with proper `<th scope="col|row">` markup, linked via `aria-describedby`. Place a button: "Afficher les données en tableau" to toggle visibility.
- Use **D3.js axis generators** which output SVG `<text>` elements natively — screen readers can parse text nodes. Avoid bitmap-rendered axis labels.
- Color differentiation must include **patterns/textures + text labels** (RGAA Thématique 3). Don't differentiate "scénario A vs B" by color alone.
- All charts must have a **text summary** (1-2 sentences) describing the key takeaway: "Le déficit augmente de 12 milliards en année 2, puis se stabilise."

**Warning signs:**
- Charts use `<canvas>` exclusively with no adjacent `<table>`.
- Color is the only differentiator between data series.
- No `role="img"` on SVG chart containers.
- Screen reader testing was not part of QA.
- "We'll do accessibility in a later phase."

**Phase to address:**
Phase 4 (Charting/Visualization). Accessibility is a build-time requirement, not a remediation task. Include screen-reader UAT in the definition of done for every chart component.

---

### Pitfall 5: Dynamic Slider → Screen Reader Chaos

**What goes wrong:**
Continuous slider updates fire `input` events at 60fps (every ~16ms). Each event triggers chart recomputation and DOM updates. Screen readers attempt to announce every change, causing a deafening flood of spoken updates ("1%... 1.2%... 1.3%...") that makes the interface unusable for blind users. Keyboard users also suffer — focus changes or value announcements pile up faster than assistive tech can process.

**Why it happens:**
WAI-ARIA `aria-valuenow` on sliders is meant to be updated as the value changes, but the WGAC expectation is that updates are **user-initiated and at human timescales** (stopped dragging, or stepped). The `<200ms real-time update` constraint creates an inherent tension: the machine needs rapid feedback, but assistive technology needs stable, debounced information. Teams test with mouse input and never test with a screen reader on rapid slider movements.

**How to avoid:**
- **Dual update strategy:** Update the visual chart at 60fps (for sighted mouse users) but **debounce ARIA announcements to 500ms** (or on `change` event, not `input` event). The slider's `aria-valuetext` should update only on drag-end (`change` event), not drag-move (`input` event).
- Implement **step-based keyboard controls**: Arrow keys adjust slider by discrete steps (e.g., 0.5% IR increments) with `aria-valuenow` updating per step. This is both accessible and gives precise control.
- Provide **text input fallback** next to each slider (a read-write `<input type="number">` field) so keyboard-only users can type exact values without dragging.
- All sliders must have `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and `aria-valuetext` attributes. The `aria-valuetext` should be human-readable: "Taux d'impôt sur le revenu : 14%" not just "14".

**Warning signs:**
- Slider `input` events trigger DOM updates at full frame rate.
- No `change` event differentiation from `input` event.
- Slider component lacks keyboard bindings (Home, End, arrows).
- Screen reader testing shows "chatter" (rapid consecutive announcements).

**Phase to address:**
Phase 4 (UI Components — sliders). Build slider component with accessibility contract (ARIA attributes + keyboard + debounced announcements) before connecting to the engine.

---

### Pitfall 6: Browser Fingerprinting via WASM Memory Patterns

**What goes wrong:**
The project proudly claims "zero personal data leaves your browser." But deterministic WASM computation of a unique reform scenario + a specific synthetic profile index produces a timing signature (computation time variations by profile), a memory access pattern, and an output vector that, when combined with browser fingerprinting (canvas fingerprint, WebGL fingerprint, font enumeration), allows a motivated observer to correlate sessions. If the same person visits multiple times with similar reform choices, their "anonymous" interaction produces a recognizable computational fingerprint.

**Why it happens:**
Privacy by Design is interpreted as "no network requests with personal data." But side channels exist: computation time varies by profile (a complex household with multiple income sources takes longer to simulate), the order of synthetic profile queries reveals interest patterns, and local storage or IndexedDB can persist derived results that constitute personal data under GDPR (even if the original input wasn't stored). Teams also often embed analytics (Plausible, Matomo) or CDN logs that, while "anonymous," correlate session timestamps with IP addresses. The CNIL considers ANY persistent client-side state that relates to an identifiable person as personal data processing.

**How to avoid:**
- **Constant-time simulation**: Pad all profile computations to a fixed time budget (sleep/busy-loop to max expected duration) so timing cannot distinguish profile complexity. Less practical at 200ms budget — consider instead batching profiles and randomizing evaluation order.
- **No persistence**: Use `sessionStorage` (cleared on tab close) rather than `localStorage`. Never persist derived results. Explicitly clear WASM linear memory between sessions.
- **Randomize profile sampling order**: If the UI shows "your decile" results, use a randomly selected profile from that decile, not a deterministic index. This prevents mapping "decile 5, reform X" → specific output value across visits.
- **No analytics on the simulator page**: Drop all tracking scripts. If analytics are needed, use server-side request counting without cookies or fingerprints. Document this choice in the privacy policy.
- **Audit all `postMessage`, `BroadcastChannel`, and `SharedWorker` usage**: Cross-tab communication can leak state.
- **Content Security Policy**: Lock down `script-src`, block third-party scripts, and use `Permissions-Policy` headers to disable fingerprinting vectors.

**Warning signs:**
- `localStorage` is used anywhere in the app.
- Analytics scripts (even "privacy-friendly") on the simulator page.
- Profile evaluation order is deterministic.
- No CSP headers configured.
- The privacy statement only mentions "no server-side storage" but not side channels.

**Phase to address:**
Phase 5 (Security & Privacy Audit). Must include browser side-channel analysis, CSP hardening, and CNIL compliance review. This cannot be done as a final checkbox — privacy architecture needs to constrain all earlier phases.

---

### Pitfall 7: Version Mismatch Between Legislation Parameters and Synthetic Population

**What goes wrong:**
The synthetic population is generated from 2023 tax data (revenus 2022). The legislation parameters (barèmes IR, plafonds, seuils) are updated to 2026 values. The simulation runs successfully — no errors, all variables resolve. But results are nonsense because profiles generated under 2023 thresholds are being evaluated against 2026 rules without reweighting for legislative drift (e.g., a 2023 "foyer à 28K€" is in a different decile under 2026 brackets).

**Why it happens:**
Synthetic data generation and legislation-as-code are treated as independent pipelines with different update cadences. The OpenFisca parameter tree is versioned (and can be updated frequently), while the synthetic population is a one-time artifact (expensive to regenerate). Teams validate each component in isolation but never validate the **joint** distribution of population × legislation × year.

**How to avoid:**
- **Version-lock the simulated year:** Select a single reference year for the synthetic population and freeze legislation parameters to match. If the population is 2023-based, simulate 2023 rules. Project forward only via explicit revalorisation/inflation parameters (which OpenFisca supports natively via `Parameter` date indexing).
- **Metadata coupling:** The synthetic dataset carries a `reference_year` field. The legislation parameter tree carries a `parameter_year` field. At simulation initialization, assert they match (or warn loudly if they don't).
- **Regression test suite:** Maintain a set of "canonical profiles" (10-20 hand-crafted households with known expected outcomes) that are validated against the official tax simulator (impots.gouv.fr simulator) for the reference year. Run these as CI tests on every parameter update.

**Warning signs:**
- No cross-reference between data generation pipeline and legislation pipeline.
- Different teams/people own each pipeline.
- Simulation "works" but no ground-truth validation exists.

**Phase to address:**
Phase 2 (Synthetic Population) and Phase 1 (Rules Engine) must define a shared contract for year alignment. Phase 6 (Integration/Validation) must include joint validation tests.

---

### Pitfall 8: Testing WASM Behavior Only Through the JS Bridge

**What goes wrong:**
All tests exercise the microsimulation engine through the wasm-bindgen JS interface. Bugs in Rust logic are indistinguishable from bugs in JS↔WASM serialization. Debugging requires a browser or Node.js with WASM support. Native Rust `#[test]` functions can't run because code uses `web_sys` or `wasm_bindgen` exclusively. Development velocity plummets as every code change requires a full `wasm-pack build` + browser reload cycle.

**Why it happens:**
The Rust WASM book's tutorial pattern encourages writing all logic behind `#[wasm_bindgen]` annotations. Teams follow this pattern and end up with a codebase where even pure math functions (interpolation, tax bracket search) are coupled to the WASM boundary. Testing requires `wasm-bindgen-test` in a headless browser, which is 10-100x slower than native `cargo test`.

**How to avoid:**
- **Split the crate into a `core` library crate and a `wasm` binding crate.** The `core` crate is pure Rust with no WASM dependencies, uses `#[cfg(test)]` native tests, and exposes clean traits. The `wasm` crate wraps `core` with `wasm_bindgen` glue, and its tests only verify the boundary layer (serialization, memory management).
- Every math-heavy function (bracket search, interpolation, tax formula) lives in `core` with native `#[test]` + property-based tests (`proptest` or `quickcheck`).
- The `wasm` crate tests verify: (a) round-trip serialization, (b) panic hook behavior, (c) memory allocation limits. Not business logic.
- In `Cargo.toml`: `[lib] crate-type = ["cdylib", "rlib"]` so native tests can link against the rlib.

**Warning signs:**
- All Rust source files import `wasm_bindgen`.
- `cargo test` fails because `wasm_bindgen` macros can't resolve.
- No `proptest` or property-based tests in the codebase.
- Every bug fix requires a browser reload to verify.

**Phase to address:**
Phase 1 (Microsimulation Engine). The crate split into `core` / `wasm` must be established before any significant business logic is written.

---

### Pitfall 9: Ignoring the Curse of Dimensionality in the Look-Up Table

**What goes wrong:**
The initial design calls for a look-up table over 8 fiscal parameters (IS rate, IR brackets × 3, TVA rate, CSG rate, carbon tax, inheritance tax). The team plans 10 grid points per dimension. That's 10^8 = 100 million pre-computed points. At 8 bytes per f64 and 4 output variables, the matrix is ~3.2 GB. This cannot be downloaded to a browser, let alone interpolated in real time.

**Why it happens:**
Teams think in terms of "more dimensions = more accurate" without internalizing the exponential growth of a Cartesian product grid. The Mésange model's shock matrix was designed for economists running batched scenarios, not for interactive 8-dimensional interpolation in a browser. The PRD mentions "interpolation multi-linéaire" without specifying the dimensionality constraint.

**How to avoid:**
- **Limit interactive dimensions to ≤4.** The remaining fiscal parameters are "scenario presets" — fixed at predefined values (e.g., "TVA standard à 20%" vs "TVA à 22%") rather than continuous sliders.
- **Use sparse grid techniques** (Smolyak sparse grids, adaptive sparse grids) which achieve comparable accuracy with exponentially fewer grid points. A level-3 sparse grid over 8 dimensions uses ~10³ points, not 10⁸.
- **Dimensionality reduction:** Pre-compute the macro matrix at a higher resolution for the top 3-4 most impactful parameters (by sensitivity analysis) and coarser for the rest.
- **Progressive loading:** Ship a low-resolution matrix (~500 KB) for initial interactivity, then stream higher-resolution points from a CDN as the user explores specific regions of the parameter space.
- Measure the matrix size at build time and fail CI if it exceeds 5 MB (compressed).

**Warning signs:**
- "We'll add more sliders later" — feature creep on dimensions.
- No byte-size budget for the look-up table.
- No dimensionality bound documented in the architecture.

**Phase to address:**
Phase 3 (Macro Integration). Define dimensionality budget in the SPEC.md before implementation. Sparse grid library selection is a key technical decision.

---

### Pitfall 10: Accessible ≠ Automated-Tool-Passing

**What goes wrong:**
The project runs axe-core / Lighthouse automated accessibility audits and passes with 100%. The team declares RGAA compliance. But actual screen reader users cannot use the app because: (a) the chart-to-table toggle is technically present but buried under 5 tab stops, (b) the data table uses `display: none` (removed from accessibility tree despite being "accessible" in source), (c) slider ARIA attributes are present but the `aria-valuetext` says "45" instead of "Taux de CSG : 4,5%", (d) dynamic chart updates aren't announced via `aria-live` regions.

**Why it happens:**
Automated tools catch ~30% of accessibility issues (color contrast, missing alt text, duplicate IDs). The remaining 70% require human judgment: Is the alternative text *meaningful*? Is the focus order *logical*? Is the live region *comprehensible*? Teams treat accessibility as a linting check rather than a UX discipline. The RGAA mandates a human audit — automated tools are insufficient for legal compliance.

**How to avoid:**
- **Hire or contract a certified RGAA auditor** for at least two audits: one during design/wireframe review and one before launch.
- **Conduct screen reader UAT** with actual assistive technology users (not just developers with VoiceOver). Test with NVDA + Firefox, JAWS + Chrome, and VoiceOver + Safari.
- **Implement `aria-live="polite"` regions** for dynamic content: chart summaries, result updates, error messages. Ensure they use `aria-atomic="true"` when full context is needed.
- **Tab through the entire interface** using only a keyboard. Verify that every interactive element is reachable and operable (including chart toggles, slider fine-adjustments, and data table sorting).
- The "Accessibility" acceptance criteria in every user story must include: "Verified with [specific AT + browser] that [specific interaction] is announced and operable."

**Warning signs:**
- Only automated tools used for accessibility validation.
- No budget for human accessibility audit.
- "We'll test with a screen reader before launch."
- ARIA attributes are copy-pasted from Stack Overflow without understanding.

**Phase to address:**
All UI phases (4, 5, 6). Accessibility is not a phase — it's a cross-cutting constraint that gates every UI deliverable.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single monolithic Rust crate (no core/wasm split) | Faster initial setup | Tests require browser; debugging is painful; refactoring is risky | Never for this project. The complexity of the tax engine demands separable testing. |
| Canvas-only charts with "alt text" | Fast chart implementation | Fails RGAA 1.1, 1.3; screen reader users abandoned | Never. RGAA compliance is a legal requirement. |
| Post-hoc DP noise injection (not DP-SGD) | Simpler data pipeline | Privacy guarantee is invalid; CNIL non-compliance | Never. DP must be woven into the generation process. |
| Hardcoded 2023 fiscal parameters | Quick prototype | Simulation results are stale on launch | Only during Phase 1 PoC with clear deprecation plan. |
| No privacy budget tracking | Simpler architecture | Effective ε unbounded; CNIL non-compliance | Never. The CNIL requires transparency about privacy loss. |
| Single-threaded WASM (no Web Workers) | Simpler message passing | Main thread blocks during 200ms computation; UI jank | Only if all computations are verified <50ms on target hardware. |
| Skipping WASM .wasm size optimization (`wasm-opt`, LTO) | Faster build times | 5-10 MB initial download on mobile; unacceptable for public service | During development with `--debug` builds only. |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenFisca JSON parameters → Rust structs | Manually writing deserialization that silently ignores unknown fields, losing legislation parameters | Use `serde` with `#[serde(deny_unknown_fields)]` and CI tests that parse the full parameter tree from a known-good OpenFisca-France version. |
| Python PolicyEngine/OpenFisca logic → Rust reimplementation | Subtly different behavior due to Python float semantics vs Rust f64, or different iteration order in dicts → hash maps | Maintain a bilingual test suite: run identical inputs through both Python (reference) and Rust (WASM) engines, compare outputs with tolerance. CI gate on exact match within 1e-6 for all canonical profiles. |
| WASM memory → JavaScript ArrayBuffer | Trying to pass large arrays (>4KB) through wasm-bindgen by value (serialized) rather than by reference (shared memory) | Use `wasm_bindgen::Memory` and `Uint8Array` views for large data transfers. Return pointers + lengths, not cloned vectors. |
| Mésange shock matrix → interpolation engine | The Mésange team provides CSV exports in French number format (comma decimal separator, space thousands). Parsing with `,` as delimiter breaks. | Normalize all economic data to a single locale-agnostic format (CSV with `.` decimal, no thousands separator) in an ingestion pipeline step. Validate with checksums. |
| Chart library ↔ reactive framework | Using Chart.js imperatively in a React/Svelte/Vue component lifecycle causes double-renders, memory leaks, and stale references | Use a reactive chart wrapper that manages the Chart.js instance lifecycle via `onMount`/`onDestroy`. Destroy and recreate on data change, don't mutate in place. |
| Synthetic data generation ↔ simulation engine | The GAN generates profiles with impossible combinations (e.g., unemployed person with "revenus d'activité > 0") that the simulation silently handles via OpenFisca fallbacks, producing subtly wrong aggregates | Run a validation pass on generated profiles: each must be a valid input for the simulation (no contradictory variable combinations). Reject and regenerate invalid profiles. |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| WASM module instantiation on every page load | 2-5s blank screen before interactivity | Compile WASM once, cache via `WebAssembly.compileStreaming` + `instantiate`. Use `wasm-pack build --target web` for ES module integration. | At 5MB .wasm on 3G mobile (common for public service users). |
| 50,000 profile simulation per slider update | Latency spikes to 2-5 seconds | Run profile simulation in **Web Worker** with batching (chunk of 5000 profiles per frame). Interpolate between slider positions for smooth visual while worker catches up. Show "calcul en cours" indicator. | When users drag sliders rapidly — backpressure from queued simulations. |
| Full reform re-evaluation for every profile on every slider change | O(slider_count × profile_count) per frame | Pre-compute the marginal impact matrix (derivative of each output w.r.t. each slider) and use first-order Taylor approximation for small slider moves. Full re-evaluation only on slider >10% change. | With 12 sliders × 50K profiles = unnecessary 600K evaluations at 60fps. |
| Loading full synthetic population into main thread memory | >500 MB RAM usage → mobile browser crash | Profile data stays in Web Worker. Main thread only receives aggregated statistics (decile tables, Gini, etc.) as compact TypedArrays. | On devices with <2 GB RAM (typical for budget-conscious users). |
| Uncompressed look-up table in WASM binary | 10+ MB .wasm file; 30s download on slow connection | Compress the matrix with LZ4 or zstd, decompress lazily during interpolation. Ship `.wasm.gz` with `Content-Encoding: gzip`. Use `wasm-opt -Oz`. | On 3G connections or metered data plans. |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Shipping raw JSON/YAML parameter files with unused/experimental legislation | Attack surface: deprecated parameters reveal internal development choices; could be misinterpreted by political opponents as "hidden features" | Tree-shake the parameter tree: only include parameters referenced by active variables. Publish the curation script for auditability. |
| WASM panic → `unreachable` trap → memory snapshot leak | If a WASM panic occurs, the entire linear memory is dumped in the browser console. For 50K-profile simulations, this contains aggregated derived data that could reveal income distributions. | Install `console_error_panic_hook` only in development builds. In production, catch panics with `std::panic::set_hook` and return a controlled error code — never dump memory. |
| Third-party npm dependency with analytics/tracking | An innocent charting library or slider component includes telemetry that phones home with interaction data (which sliders were moved, to what values). Under GDPR, slider positions + IP = personal data. | Audit all npm dependencies for network requests. Lock down with CSP `connect-src 'self'`. Use `npm audit` + manual review of any dependency making outbound requests. |
| CDN hosting of `.wasm` → supply chain risk | If the WASM binary is served from a CDN (jsDelivr, unpkg), an attacker who compromises the CDN can replace it with a malicious WASM that exfiltrates user data from linear memory back to an attacker-controlled server. | Self-host the `.wasm` binary on the same origin. Use Subresource Integrity (SRI) hashes if CDN is unavoidable. |
| `localStorage` caching of simulation results | Users' derived tax outcomes are stored locally. Under CNIL guidance, tax impact calculations constitute personal data. LocalStorage persists indefinitely and across sessions. | Use `sessionStorage` only. Explicitly clear simulation state on tab close. Add a prominent "Effacer mes données" button. |
| URL hash / query parameter reflects simulation state | Users share URLs with `?ir=14&tva=20&is=25` — these become de facto personal data when shared. Privacy impact: social graph inference from shared URLs. | Use fragment-based state that is not sent to the server (already standard for SPAs). Add a warning: "Ce lien contient les paramètres de votre simulation." |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| "Déficit budgétaire : +42.7 Mds€" without context | Citizens don't know if 42.7 billion is a big number relative to GDP (€2800B) or the total budget (€1700B) | Always show numbers with context: "Déficit : +42,7 Mds€ (soit 1,5% du PIB / 2,5% du budget de l'État)". Use visual scale (horizontal bar showing size relative to total budget). |
| Sliders for every tax parameter with equal visual weight | Users are overwhelmed — paralysis of choice. Most citizens don't know the difference between CSG and CRDS. | Tier 1: 3-4 "macro sliders" (Niveau d'imposition global, Niveau de dépenses, Taxation du capital). Tier 2 (expert mode): detailed sliders for specific taxes. |
| "Impact sur votre foyer" with no income input | User sees "vous gagneriez 230€" but hasn't entered their income. The label implies personalization without personal data. | Clearly label: "Impact estimé pour un foyer type avec 28K€ de revenus." Provide an option to customize with "Mon foyer ressemble à..." |
| Silent loading states during WASM computation | User moves slider, nothing happens for 500ms, then chart jumps. User thinks the app is broken. | Immediate skeleton/spinner on slider interaction. Show "Calcul en cours..." with subtle progress indicator. Update chart atomically when done (no partial rendering). |
| "Mode expert" as a simple toggle | Users toggle expert mode and face an impenetrable wall of acronyms (PIB, PIB/hab, solde primaire, solde structurel, multiplicateur keynésien). | Progressive disclosure: expert mode reveals parameters one category at a time. Each parameter has a "?" tooltip with vulgarized explanation. Offer "Vue simplifiée" as the default. |

---

## "Looks Done But Isn't" Checklist

- [ ] **WASM Engine:** Compiles and runs — but verified with bilingual Python→Rust output comparison for ALL canonical profiles? (Cross-language validation suite)
- [ ] **WASM Engine:** Passes cargo test — but `cargo test` runs native tests (not WASM), and `wasm-pack test` passes separately? (Dual test target)
- [ ] **Interpolation Engine:** Returns values — but returns `Option::None` or clamped warning when outside the convex hull? (Bounds validation)
- [ ] **Synthetic Population:** 50,000 profiles generated — but DP training used DP-SGD (not post-hoc noise), and ε budget is documented? (CNIL-compliant DP)
- [ ] **Synthetic Population:** Profiles look realistic — but validation checks that no profile combines contradictory variables (unemployed with salary >0)? (Profile validation)
- [ ] **Dashboard Charts:** Beautiful on screen — but each chart has an accessible HTML table fallback AND passes screen reader UAT? (RGAA 1.1, 1.3)
- [ ] **Dashboard Charts:** Color-coded data series — but each series is also differentiated by pattern/texture AND text label? (RGAA Thématique 3)
- [ ] **Sliders:** Smooth dragging — but `aria-valuetext` updates only on drag-end, and keyboard controls work (arrow keys, Home, End)? (RGAA Thématique 11)
- [ ] **Privacy:** No POST requests with personal data — but also no `localStorage`, no analytics scripts, no CDN that logs IPs, no timing side channels? (Privacy by Design audit)
- [ ] **Privacy:** "Aucune donnée personnelle ne quitte votre navigateur" — but also no fingerprintable computation patterns persist across sessions? (Side-channel audit)
- [ ] **RGAA Compliance:** axe-core passes at 100% — but a human RGAA auditor has reviewed all 106 criteria? (Human audit)
- [ ] **Performance:** Single-profile simulation <200ms — but verified under 12-slider rapid drag with 50K-profile evaluation in background? (Load test)
- [ ] **Year Consistency:** Simulation runs — but the synthetic population `reference_year` matches the legislation `parameter_year`? (Version coupling check)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| WASM serialization tax | MEDIUM | Refactor boundary to batch interface. Weeks 2-3 of Phase 1. Easier if caught early via profiling. |
| Extrapolation outside grid | LOW | Add bounds check in interpolation function + UI warning. One sprint. Harder if users have already seen (and shared) invalid results. |
| DP budget exhaustion | HIGH | Needs redesign of query architecture — pre-computed aggregates with one-time DP noise. May require regenerating the synthetic dataset. 4-6 weeks. THIS IS A REWRITE-LEVEL RISK. |
| Canvas-only charts (accessibility) | MEDIUM-HIGH | Generate HTML tables for all charts + ARIA annotations. 2-3 sprints. Harder if chart library doesn't support data table extraction. |
| Slider screen reader chaos | LOW-MEDIUM | Debounce ARIA updates, add keyboard controls. One week. Low complexity but requires AT testing. |
| Browser fingerprinting via WASM | HIGH | Requires architectural change: constant-time computation, stateless execution, CSP hardening. 3-4 weeks. Hard to retrofit; privacy must be designed in. |
| Version mismatch (population vs legislation) | MEDIUM | Re-run population generation with matched year OR backdate legislation. 2-3 weeks. Simpler if caught early via version metadata. |
| Curse of dimensionality (look-up table) | HIGH | Switch to sparse grid methods or reduce interactive dimensions. May require re-running Mésange pre-computation. 4-8 weeks. THIS IS A REWRITE-LEVEL RISK. |
| Untestable WASM logic | MEDIUM | Extract core crate from WASM crate. 1-2 weeks of refactoring. Painful but mechanical. |
| Automated-only accessibility testing | LOW-MEDIUM | Schedule human audit + AT UAT sessions. 2-3 weeks. Low technical cost, but requires finding accessibility experts. |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| WASM serialization tax | Phase 1 (Microsimulation Engine) | Profiling benchmark: JS↔WASM boundary <1ms per full reform object |
| Extrapolation beyond grid | Phase 3 (Macro Integration) | Unit test: out-of-bounds input returns `None` or clamped value with warning |
| DP budget exhaustion | Phase 2 (Synthetic Population) | Privacy budget report: total ε consumed across all dashboard queries < 1.0 |
| Canvas-only inaccessible charts | Phase 4 (UI/Visualization) | Screen reader UAT: every chart navigable and comprehensible |
| Slider screen reader chaos | Phase 4 (UI Components) | AT test: slider announces value only on drag-end; keyboard steps work |
| Browser fingerprinting | Phase 5 (Security/Privacy) | Side-channel audit: no deterministic computation patterns across sessions |
| Version mismatch population/legislation | Phase 2 + Phase 1 contract | CI gate: assert population.year == legislation.year |
| Curse of dimensionality | Phase 3 (Macro Integration) | Build-time check: matrix_size < 5 MB compressed; dims ≤ 4 |
| Untestable WASM logic | Phase 1 (Microsimulation Engine) | `cargo test` passes without WASM; `wasm-pack test` passes boundary layer only |
| Automated-only accessibility | All UI phases | Human RGAA audit report filed before each milestone completion |
| Year consistency (legislation drift) | Phase 6 (Integration) | Integration test: match canonical profiles against reference simulator |

---

## Sources

### Rules as Code → WASM
- Rust and WebAssembly Book (rustwasm.github.io/docs/book/) — debugging, profiling, code size, JS interop sections. [OFFICIAL, HIGH]
- wasm-bindgen Guide (github.com/rustwasm/wasm-bindgen) — reference for JS snippets, types, and boundary behavior. [OFFICIAL, HIGH]
- OpenFisca Core GitHub (github.com/openfisca/openfisca-core) — architecture and Python ecosystem context. [OFFICIAL, HIGH]
- PolicyEngine Core GitHub (github.com/PolicyEngine/policyengine-core) — fork evolution, optimization patterns. [OFFICIAL, HIGH]
- Rust WASM book sunsetting notice (blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/) — ecosystem status 2025-2026. [OFFICIAL, HIGH]

### Macro Look-up Tables & Interpolation
- Mésange model documentation (Insee/DGT) — referenced in PRD section 4-5. [OFFICIAL, HIGH]
- Numerical Recipes, Chapter 3: Interpolation and Extrapolation — mathematical foundation for multi-linear interpolation. [REFERENCE, HIGH]
- Smolyak sparse grid literature — dimensionality reduction for high-dimensional interpolation. [ACADEMIC, MEDIUM]

### Synthetic Data & Differential Privacy
- Dwork et al. (2006): "Calibrating Noise to Sensitivity in Private Data Analysis" — foundational DP paper. [ACADEMIC, HIGH]
- Wikipedia: Differential Privacy — composition theorems, Laplace mechanism, group privacy. [REFERENCE, HIGH]
- CNIL guidance on synthetic data (cnil.fr) — French regulatory position: synthetic data is not automatically anonymous. [OFFICIAL, HIGH]
- Abadi et al. (2016): "Deep Learning with Differential Privacy" — DP-SGD for generative models. [ACADEMIC, HIGH]
- PRD Section 7: Synthèse des Données et Stratégies de Conformité RGPD — IPF, copulas, GAN, VAE, membership inference attacks. [PROJECT, HIGH]

### Accessible Data Visualizations
- W3C WAI Introduction to Web Accessibility (w3.org/WAI/fundamentals/accessibility-intro/) [OFFICIAL, HIGH]
- W3C WAI Tutorials: Custom Controls (w3.org/WAI/tutorials/forms/custom-controls/) — ARIA patterns for interactive controls. [OFFICIAL, HIGH]
- RGAA 4.1.2 — Critères 1.1, 1.3, Thématiques 3, 8, 11 — French legal requirements for public services. [OFFICIAL, HIGH]
- PRD Section 5: Ingénierie de l'Accessibilité — canvas/SVG/ARIA/animation requirements. [PROJECT, HIGH]

### Privacy-Preserving Client-Side Computation
- PRD Section 6: Décentralisation de l'Exécution — WASM Privacy by Design rationale. [PROJECT, HIGH]
- GDPR Article 4(1) — definition of personal data; Article 25 — Data Protection by Design. [OFFICIAL, HIGH]
- CNIL guidance on browser fingerprinting and local storage as personal data processing. [OFFICIAL, MEDIUM]

---

*Pitfalls research for: Simulateur Budgétaire Citoyen (Civic Budget Simulator)*
*Researched: 2026-05-11*
*Prevention strategies mapped to roadmap phases 1-6*
