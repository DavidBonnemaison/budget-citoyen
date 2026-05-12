---
phase: 01-data-foundation-rules-engine
plan: 03
subsystem: data-pipeline
tags: [shock-matrix, var-bootstrap, convex-hull, parquet, zstd, numpy, scipy, pyarrow, statsmodels]

# Dependency graph
requires:
  - phase: 01-data-foundation-rules-engine
    provides: "pyproject.toml with dependencies (numpy, scipy, pyarrow, pandas), project structure"
provides:
  - "VAR bootstrap estimation for Mesange-derived shock propagation vectors"
  - "3D/4D grid construction with max 4 interactive fiscal dimensions (10-15 breakpoints)"
  - "Smolyak sparse grid with Clenshaw-Curtis nodes and Cartesian fallback"
  - "Convex hull computation via scipy.spatial.ConvexHull with bounds documentation"
  - "Parquet/Zstd export with compression_level=9, <5 MB size assertion"
  - "Sidecar metadata JSON with shockmatrix-v2025.1 version tag and reference year 2025"
affects: ["02-wasm-engines", "macroeconomic projections", "Phase 2 macro interpolation"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optional dependency pattern: try/except ImportError with fallback (bootstrap.py for statsmodels)"
    - "Lazy imports in __init__.py with warnings for missing optional modules"
    - "NumPy float32 for grid storage (memory-efficient for browser delivery)"
    - "PyArrow Parquet with zstd compression for columnar shock matrix export"
    - "scipy.spatial.ConvexHull — never hand-roll convex hull computation"

key-files:
  created:
    - "packages/data-pipeline/src/shock_matrix/__init__.py"
    - "packages/data-pipeline/src/shock_matrix/bootstrap.py"
    - "packages/data-pipeline/src/shock_matrix/grid_build.py"
    - "packages/data-pipeline/src/shock_matrix/convex_hull.py"
    - "packages/data-pipeline/src/shock_matrix/export_parquet.py"
  modified:
    - ".gitignore"

key-decisions:
  - "Placeholder shocks from public INSEE/DG Tresor data used for v1 when Mesange model is unavailable (D-11 fallback)"
  - "Cartesian grid as primary format with Smolyak sparse grid support via Clenshaw-Curtis nodes (D-10)"
  - "4-dimension hard cap enforced via assertions in both build_cartesian_grid and build_smolyak_grid (D-08)"
  - "10-15 breakpoints per dimension, default 12, enforced via ValueError (D-09)"
  - "PyArrow Parquet/Zstd at compression_level=9 with <5 MB size assertion (D-09)"
  - "shockmatrix-v2025.1 version tag, reference year 2025 locked (D-15, D-16)"

patterns-established:
  - "Pattern 1: Optional dependency imports — main deps (pyarrow, statsmodels) wrapped in try/except with clear error messages directing users to install or use fallback"
  - "Pattern 2: Grid abstraction — Cartesian and Smolyak grid formats supported by a common build_dimension_breakpoints() + per-format builder pattern"
  - "Pattern 3: Metadata-rich export — all artifacts carry reference_year, version tag, breakpoints, convex hull bounds, and compression stats in sidecar JSON"

requirements-completed: [DATA-04]

# Metrics
duration: ~15min
completed: 2026-05-12
---

# Phase 1 Plan 3: Shock Matrix Pre-Computation Pipeline Summary

**VAR bootstrap estimation, Smolyak/Cartesian grid construction, scipy convex hull bounds, and Parquet/Zstd compressed export — the Mesange-derived shock matrix ready for Phase 2 macro interpolation**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-12T07:13:00Z
- **Completed:** 2026-05-12T07:28:59Z
- **Tasks:** 2
- **Files modified:** 6 (5 new + 1 modified)

## Accomplishments

- VAR bootstrap module with statsmodels integration and INSEE-derived placeholder fallback for v1
- Cartesian and Smolyak sparse grid construction with hard 4-dimension cap and 10-15 breakpoint enforcement
- Convex hull computation via scipy.spatial.ConvexHull with out-of-bounds detection and Markdown bounds reporting
- Parquet/Zstd export with compression_level=9, <5 MB assertion, and sidecar metadata JSON (shockmatrix-v2025.1)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create VAR bootstrap estimation and grid construction modules** - `cc1ff37` (feat)
2. **Task 2: Create convex hull computation and Parquet/Zstd export with sidecar metadata** - `1bc30e6` (feat)

**Plan metadata:** _to be committed after SUMMARY.md_

## Files Created/Modified

- `packages/data-pipeline/src/shock_matrix/__init__.py` - Lazy imports for all 5 modules with graceful degradation
- `packages/data-pipeline/src/shock_matrix/bootstrap.py` - VAR bootstrap (statsmodels) + placeholder shocks (INSEE public data), confidence bounds
- `packages/data-pipeline/src/shock_matrix/grid_build.py` - Cartesian/Smolyak grid construction, max 4 dims, 10-15 breakpoints per dimension
- `packages/data-pipeline/src/shock_matrix/convex_hull.py` - scipy.spatial.ConvexHull wrapper, out-of-bounds mask, Markdown bounds report
- `packages/data-pipeline/src/shock_matrix/export_parquet.py` - PyArrow Parquet/Zstd export, sidecar metadata JSON, <5 MB assertion
- `.gitignore` - Python cache, venv, IDE, parquet/metadata outputs

## Decisions Made

- Placeholder shocks derived from public INSEE comptes nationaux and DG Tresor macro projections with plausible sign patterns (tax increase → negative GDP, spend increase → positive GDP). Clearly labeled as "placeholder" in metadata per D-11.
- Clenshaw-Curtis nodes used for Smolyak sparse grid construction (standard choice for numerical integration). Falls back to Cartesian if construction fails.
- Axis-aligned bounding box used as degenerate hull fallback when Qhull fails on collinear/coplanar points.
- Optional dependencies (pyarrow, statsmodels) wrapped in try/except imports with clear error messages. `__init__.py` uses warnings for missing modules rather than blocking import.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added .gitignore for Python project hygiene**
- **Found during:** Task 1 commit
- **Issue:** No .gitignore existed — `__pycache__/` directories, `.venv/`, `*.parquet`, and IDE files would pollute the repository
- **Fix:** Created .gitignore with Python, venv, IDE, OS, and data pipeline output patterns
- **Files modified:** `.gitignore` (new)
- **Verification:** `git status` no longer shows `__pycache__/` as untracked
- **Committed in:** `cc1ff37` (Task 1 commit)

**2. [Rule 3 - Blocking] __init__.py imported modules not yet created**
- **Found during:** Task 1 first execution
- **Issue:** `__init__.py` eagerly imported `convex_hull` and `export_parquet` modules that didn't exist yet during Task 1
- **Fix:** Refactored to lazy imports with try/except ImportError and warnings for missing modules. Updated during Task 2 to make the imports work.
- **Files modified:** `packages/data-pipeline/src/shock_matrix/__init__.py`
- **Verification:** `from shock_matrix.bootstrap import ...` succeeds without convex_hull.py present
- **Committed in:** `cc1ff37` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for project hygiene and modular development. No scope creep.

## Issues Encountered

- Python 3.9.6 (system default) cannot install PyArrow 24.0.0 (requires ≥3.10). Created a Python 3.13 virtual environment via Homebrew to satisfy dependency requirements. Production deployment should use Python ≥3.10.
- statsmodels not available in system Python — installed via pip in virtual environment. Module gracefully handles missing statsmodels with placeholder fallback.

## User Setup Required

None - no external service configuration required. The data pipeline runs as an offline batch process using Python packages listed in `pyproject.toml`.

## Next Phase Readiness

- Shock matrix pipeline ready for integration testing in Phase 2 (WASM macro engine).
- Placeholder shocks are sufficient for v1 prototype — production requires Mesange model access (D-11 restricted).
- Downstream dependencies: `shockmatrix-v2025.1.parquet` + `shockmatrix-v2025.1.meta.json` consumed by the WASM macro interpolator.
- All D-08 through D-16 decisions enforced in code.

---

## Self-Check: PASSED

- All 6 key files exist on disk ✓
- Task commits `cc1ff37` and `1bc30e6` found in git log ✓
- D-08: 5-dimension assertion fires correctly ✓
- D-09: Min/max breakpoint enforcement (10-15 range) ✓
- D-09: Size assertion `5_000_000` in export_parquet.py ✓
- D-10: `scipy.spatial.ConvexHull` import in convex_hull.py ✓
- D-16: `shockmatrix-v2025.1` version tag in export_parquet.py ✓
- Plan verification script passes (placeholder shocks, grid build, convex hull, Parquet export) ✓
- All acceptance criteria satisfied ✓

---

*Phase: 01-data-foundation-rules-engine*
*Completed: 2026-05-12*
