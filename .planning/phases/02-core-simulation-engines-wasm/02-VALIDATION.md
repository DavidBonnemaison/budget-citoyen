---
phase: 2
slug: core-simulation-engines-wasm
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | cargo test (native Rust) + wasm-pack test (headless browser) + proptest 1.11.0 |
| **Config file** | Cargo.toml per crate (no separate test config needed) |
| **Quick run command** | `cargo test -p budget-citoyen-core` |
| **Full suite command** | `cargo test --workspace && wasm-pack test --headless packages/wasm-micro packages/wasm-macro` |
| **Estimated runtime** | ~30 seconds (native) + ~60 seconds (browser) |

---

## Sampling Rate

- **After every task commit:** Run `cargo test -p budget-citoyen-core`
- **After every plan wave:** Run `cargo test --workspace && wasm-pack test --headless packages/wasm-micro packages/wasm-macro`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | MICRO-01 | T-02-01 | IR matches OpenFisca reference at 1e-6 | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | MICRO-02 | T-02-02 | IS/TVA/cotisations match reference | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | MICRO-03 | T-02-03 | Aides sociales match reference | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | MICRO-04 | T-02-04 | No fetch/network from workers | architecture | Manual verification + CSP audit | N/A | ⬜ pending |
| 02-01-05 | 01 | 1 | MICRO-05 | T-02-05 | <200ms single-profile calc | performance | `wasm-pack test` with timing assertion | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | MACRO-01 | T-02-06 | Deficit trajectory interpolation | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | MACRO-02 | T-02-07 | Debt trajectory interpolation | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | MACRO-03 | T-02-08 | GDP and employment projections | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 1 | MACRO-04 | T-02-09 | Macro interpolation < 50ms | performance | `wasm-pack test` with timing assertion | ❌ W0 | ⬜ pending |
| 02-02-05 | 02 | 1 | MACRO-05 | T-02-10 | No real-time rate variation code | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `packages/core/Cargo.toml` — Crate initialization
- [ ] `packages/core/tests/bilingual_tests.rs` — Bilingual validation harness
- [ ] `packages/core/tests/parameter_tests.rs` — proptest strategies
- [ ] `packages/core/tests/profile_tests.rs` — Profile validation edge cases
- [ ] `packages/wasm-micro/Cargo.toml` — WASM crate initialization
- [ ] `packages/wasm-micro/tests/wasm_boundary.rs` — JS↔WASM boundary tests
- [ ] `packages/wasm-macro/Cargo.toml` — WASM crate initialization
- [ ] `packages/wasm-macro/tests/interpolation_tests.rs` — In/out-of-bounds tests
- [ ] `packages/wasm-macro/tests/wasm_boundary.rs` — WASM boundary tests
- [ ] `Cargo.toml` — Workspace root
- [ ] `.github/workflows/phase2-wasm.yml` — CI workflow
- [ ] Rust toolchain installation verification
- [ ] Pre-commit hook: `cargo fmt --check && cargo clippy -- -D warnings`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Zero network access from WASM workers | MICRO-04 | No browser API introspection from tests | Audit worker source code for `fetch()`/`XMLHttpRequest` calls; verify CSP headers block network |
| Convex hull boundary documentation | MACRO-01 | Requires visual inspection of boundary behavior | Verify warning message contract matches CONTEXT.md D-09; test out-of-bounds slider combination returns `is_out_of_bounds: true` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
