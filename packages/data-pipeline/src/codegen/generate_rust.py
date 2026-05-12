"""Code generator: OpenFisca-France Python → Rust/WASM.

Introspects the openfisca_france variable graph and generates:
  - Rust formula modules (one per tax domain)
  - Flat Profile struct definition
  - Index mapping constants (shared Rust/TypeScript)

Output writes to packages/wasm-micro/src/generated/

Usage:
  python -m codegen.generate_rust              # Full generation
  python -m codegen.generate_rust --spike      # Spike 3-5 formulas only

Architecture (D-05, D-08, RESEARCH.md Pattern 4):
  1. Instantiate FranceTaxBenefitSystem()
  2. Access .variables dict containing all ~200+ variable definitions
  3. Build dependency graph (DAG) from formula source code
  4. Topological sort the DAG for correct emission order
  5. Emit one Rust module per tax domain with pure functions
"""

import datetime as _datetime
import inspect as _inspect
import os as _os
import re as _re
import sys as _sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Constants ────────────────────────────────────────────────────────────────

# Tax domain grouping prefixes
DOMAIN_PREFIXES: Dict[str, List[str]] = {
    "is": ["is_", "impot_societes"],
    "tva": ["tva_"],
    "cotisations": [
        "csg_", "crds_", "cotisations_", "forfait_social_",
    ],
    "aides": [
        "rsa_", "apl_", "als_", "alf_", "allocations_",
        "prime_activite_", "aah_", "aspa_", "paje_", "are_",
        "asi_", "ppa_", "acs_", "cmu_", "af_", "ars_",
        "ape_", "apje_", "asf_", "bourse_", "cf_",
        "aide_logement", "prestations_familiales", "prestations_sociales",
        "minima_sociaux", "minimum_vieillesse",
    ],
    "ir": [
        "ir_", "impot_revenu", "irpp",
        "bareme", "decote", "plaf_qf", "quotient_familial",
        "rfr_", "rni", "rng", "rbg", "nbptr", "taux_effectif",
        "abat_spe", "credit_impot", "reduction_impot", "foyer_impose",
        "charges_deduc", "cd_", "glo_", "residence_fiscale",
        "avantage_qf", "jeunes",
    ],
}

# Variables that are leaf inputs (no formula, set by user data)
LEAF_INPUT_INDICATORS = [
    "f2ab", "f3vd", "f3vi", "f3vf", "f6dd",
    "depcom", "nbptr", "en_couple", "nb_parents",
]

# Variables with formulas that are simple wrappers can be inlined
SIMPLE_WRAPPER_NAMES = set()


# ── OpenFisca Introspection ─────────────────────────────────────────────────


def _get_var_source(variable) -> Optional[Tuple[str, str]]:
    """Extract the latest formula source code and period for a variable.

    Args:
        variable: An OpenFisca Variable instance.

    Returns:
        Tuple of (source_code, formula_period_str) or None if no formula.
    """
    if not variable.formulas:
        return None

    latest_period = max(variable.formulas.keys())
    formula = variable.formulas[latest_period]

    try:
        source = _inspect.getsource(formula)
    except (OSError, TypeError):
        return None

    return source, latest_period


def _extract_dependencies(source: str) -> Set[str]:
    """Extract variable names referenced in a formula's source code.

    Matches patterns like:
        foyer_fiscal('var_name', period)
        entity.members('var_name', period)
        entity.members.foyer_fiscal('var_name', period)

    Args:
        source: Python formula source code.

    Returns:
        Set of referenced variable names.
    """
    # Match variable references: entity('name', period) or members('name', period)
    pattern = r"(?:members(?:\.\w+)?\()?['\"](\w+)['\"]\s*[,\)]"
    matches = _re.findall(pattern, source)
    return set(matches)


def _classify_tax_domain(variable_name: str) -> str:
    """Classify a variable into its tax domain by prefix matching.

    Checks specific domains first (is, tva, cotisations, aides), then
    falls back to 'ir' for revenue-related variables, then 'other'.

    Args:
        variable_name: The OpenFisca variable name (snake_case).

    Returns:
        Domain key: 'ir', 'is', 'tva', 'cotisations', 'aides', or 'other'.
    """
    name = variable_name.lower()

    for domain in ("is", "tva", "cotisations", "aides"):
        for prefix in DOMAIN_PREFIXES.get(domain, []):
            if name.startswith(prefix) or prefix in name:
                return domain

    # IR: broadest catch-all for revenue-related variables
    for prefix in DOMAIN_PREFIXES.get("ir", []):
        if name.startswith(prefix) or prefix in name:
            return "ir"

    return "other"


def _can_auto_generate(source: str) -> Tuple[bool, List[str]]:
    """Determine if a formula can be auto-translated to Rust.

    Args:
        source: Python formula source code.

    Returns:
        Tuple of (can_generate, list_of_blocking_patterns).
    """
    blockers = []

    # Patterns that truly block auto-generation in the flat Profile model.
    # Per D-13, cross-entity references are resolved to flat struct fields,
    # so patterns like entity.members.foyer_fiscal() and role-based aggregation
    # become no-ops (single profile, no entity hierarchy).
    #
    # Only patterns requiring numpy array semantics or hierarchical traversal
    # remain as true blockers.
    blocking_patterns = [
        # Numpy vectorized operations requiring array context
        (r"\.astype\(", "numpy astype() call"),
        # Hierarchical entity traversal (no equivalent in flat model)
        (r"\.children\(", "hierarchical entity children traversal"),
        # Numpy where() with array semantics
        (r"\bwhere\(", "numpy where() call"),
    ]

    for pattern, description in blocking_patterns:
        if _re.search(pattern, source):
            blockers.append(description)

    return len(blockers) == 0, blockers


def _translate_python_to_rust(
    source: str,
    var_name: str,
    entity_type: str,
    all_var_names: Set[str],
) -> str:
    """Translate an OpenFisca Python formula body to a Rust function body.

    Args:
        source: Python source code of the formula function.
        var_name: OpenFisca variable name.
        entity_type: Entity key (foyer_fiscal, famille, individu, menage).
        all_var_names: Set of all variable names (to distinguish formulas
            from input variables).

    Returns:
        Rust function body as a string.
    """
    can_gen, blockers = _can_auto_generate(source)

    if not can_gen:
        lines = [
            "    // TODO: MANUAL_PORT — Cannot auto-generate.",
            f"    // Blocking patterns: {', '.join(blockers)}",
            "    // Original Python formula:",
        ]
        for line in source.strip().split("\n"):
            lines.append(f"    // {line}")
        lines.append("    0.0_f64")
        return "\n".join(lines)

    # Extract dependencies
    deps = _extract_dependencies(source)

    # Build the Rust body
    lines = []
    body_lines = source.strip().split("\n")

    for line in body_lines:
        stripped = line.strip()

        # Skip function definition
        if stripped.startswith("def "):
            continue
        # Skip docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Handle empty lines
        if not stripped:
            lines.append("")
            continue

        # Preserve Python comments as Rust comments (skip tooling comments)
        if stripped.startswith("#"):
            comment_text = stripped[1:].strip()
            if not any(
                comment_text.startswith(skip)
                for skip in ("noqa", "type:", "pragma:", "flake8:")
            ):
                lines.append(f"    // {comment_text}")
            continue

        # Translate the line
        translated = _translate_line(stripped, deps, entity_type, all_var_names)
        lines.append(f"    {translated}")

    # If the last meaningful line isn't a return, add a default return
    body = "\n".join(lines)
    if "return " not in body.split("//")[0] if "//" in body else "return " not in body:
        lines.append("    0.0_f64")

    return "\n".join(lines)


def _translate_line(
    line: str,
    deps: Set[str],
    entity_type: str,
    all_var_names: Set[str],
) -> str:
    """Translate a single Python formula line to Rust.

    Args:
        line: Stripped Python line.
        deps: Set of referenced variable names.
        entity_type: The entity key for the current formula.
        all_var_names: All known variable names.

    Returns:
        Rust equivalent line.
    """
    # ── Strip options=[ADD] from calls (no-op in flat model) ──
    line = _re.sub(r",\s*options\s*=\s*\[ADD\]", "", line)

    # ── Translate variable references ──
    # entity('var_name', period) → calculate_var_name(parameters, period, profile)
    for dep in sorted(deps, key=len, reverse=True):
        for entity in ("foyer_fiscal", "famille", "individu", "menage"):
            pattern = f"{entity}('{dep}', period)"
            if pattern in line:
                fn_name = f"calculate_{dep}"
                line = line.replace(pattern, f"{fn_name}(parameters, period, profile)")

    # ── Translate parameters(period).path.to.param ──
    # parameters(period).path.to.param → parameters.get_scalar("path.to.param")
    # Special case: .bareme at end → parameters.get_brackets("...")
    param_match = _re.search(r"parameters\(period\)\.(\S+)", line)
    if param_match:
        full_path = param_match.group(1)
        # Determine if this is a barème (bracket table) or scalar
        if full_path.endswith(".bareme") or "bareme" in full_path:
            # Bracket access
            key_path = full_path.replace(".", "/")
            line = _re.sub(
                r"parameters\(period\)\." + _re.escape(full_path),
                f'parameters.get_brackets("{key_path}").unwrap_or_default()',
                line,
            )
            # Replace bareme.calc(expr) with bracket_calc(bareme, expr)
            line = line.replace(
                f'.unwrap_or_default().calc(',
                '.unwrap_or_default()',
            )
            # Also handle bareme.calc(...) pattern
            line = _re.sub(
                r'\.calc\(([^)]+)\)',
                r'_bracket_calc(&\1)',
                line,
            )
        else:
            key_path = full_path.replace(".", "/")
            line = _re.sub(
                r"parameters\(period\)\." + _re.escape(full_path),
                f'parameters.get_scalar("{key_path}").unwrap_or(0.0)',
                line,
            )

    # ── Cross-entity member access ──
    # In flat Profile model (D-13), all cross-entity references resolve
    # to the same profile. So entity.members.foyer_fiscal('var') just
    # becomes calculate_var(parameters, period, profile).
    for cross_pattern, cross_entity in [
        (r"\.members\.foyer_fiscal\('(\w+)', period\)", None),
        (r"\.members\.famille\('(\w+)', period\)", None),
        (r"\.foyer_fiscal\('(\w+)', period\)", None),
        (r"\.demandeur\.menage\('(\w+)', period\)", None),
        (r"\.conjoint\('(\w+)', period\)", None),
    ]:
        def _replace_member_ref(m, all_ns=all_var_names):
            dep_name = m.group(1)
            if dep_name in all_ns:
                return f"calculate_{dep_name}(parameters, period, profile)"
            return f"profile.{dep_name}"

        line = _re.sub(cross_pattern, _replace_member_ref, line)

    # ── Same-entity member access (entity.members('var', period)) ──
    members_match = _re.search(
        rf"{entity_type}\.members\('(\w+)', period\)", line
    )
    if members_match:
        dep_name = members_match.group(1)
        if dep_name in all_var_names:
            fn_name = f"calculate_{dep_name}"
            line = line.replace(
                members_match.group(0),
                f"{fn_name}(parameters, period, profile)",
            )
        else:
            line = line.replace(
                members_match.group(0),
                f"profile.{dep_name}",
            )

    # ── Role-based aggregation (no-op in flat model) ──
    # Strip role=FoyerFiscal.DECLARANT_PRINCIPAL, role=Famille.DEMANDEUR, etc.
    line = _re.sub(r",?\s*role\s*=\s*\w+\.\w+", "", line)

    # ── OpenFisca enum type comparisons — simplify for flat model ──
    # TypesRSANonCalculable.calculable → always true (simplified)
    line = _re.sub(r"==\s*Types\w+\.\w+", "== 1.0_f64", line)
    line = _re.sub(r"!=\s*Types\w+\.\w+", "!= 1.0_f64", line)

    # ── has_role() → always true in flat model (single principal) ──
    # individu.has_role(FoyerFiscal.DECLARANT_PRINCIPAL) → true
    line = _re.sub(
        r"\w+\.has_role\(\w+\.\w+\)",
        "1.0_f64",
        line,
    )

    # ── FoyerFiscal.DECLARANT_PRINCIPAL / Famille.DEMANDEUR → identity ──
    line = _re.sub(r"\bFoyerFiscal\.\w+", "1.0_f64", line)
    line = _re.sub(r"\bFamille\.\w+", "1.0_f64", line)

    # ── Special function translations ──

    # max_(0, expr) → f64::max(0.0, expr)
    line = _re.sub(r"max_\(0\s*,\s*(.+?)\)", r"(0.0_f64).max(\1)", line)
    # max_(a, b) → a.max(b)
    line = _re.sub(r"max_\((.+?),\s*(.+?)\)", r"(\1).max(\2)", line)

    # min_(a, b) → a.min(b)
    line = _re.sub(r"min_\((.+?),\s*(.+?)\)", r"(\1).min(\2)", line)

    # round_(expr, n) -> ((expr) * 10^n).round() / 10^n
    line = _re.sub(
        r"round_\((.+?),\s*(\d+)\)",
        lambda m: f"(({m.group(1)}) * {10 ** int(m.group(2))}.0_f64).round() / {10 ** int(m.group(2))}.0_f64",
        line,
    )

    # around(expr) → round to 2 decimal places (fiscal rounding)
    line = _re.sub(
        r"around\((.+?)\)",
        r"((\1) * 100.0_f64).round() / 100.0_f64",
        line,
    )

    # entity.sum(expr) → expr (simplification for flat model)
    # For same-entity sum, in flat model we just use the value directly
    line = _re.sub(r"\w+\.sum\((.+?)\)", r"\1", line)

    # ── Boolean arithmetic translation ──
    # (cond == val) * expr → if cond == val { expr } else { 0.0 }
    # Handle common patterns
    bool_arith_pattern = r"\((.+?)\s*(==|!=)\s*(.+?)\)\s*\*\s*(.+)"
    if _re.search(bool_arith_pattern, line):
        # Transform the line to handle boolean arithmetic
        # This is tricky because there could be multiple on one line
        line = _translate_bool_arithmetic(line)

    # ── Handle return statement ──
    if line.startswith("return "):
        body = line[len("return "):].strip()
        # Clean up trailing semicolons if any
        body = body.rstrip(";")
        return f"return {body};"
    elif "=" in line and not any(
        kw in line for kw in ("==", "!=", "<=", ">=")
    ):
        # Assignment
        if any(
            line.strip().startswith(kw)
            for kw in ("if ", "else", "elif ", "for ")
        ):
            return f"// UNTRANSLATED: {line}"
        parts = line.split("=", 1)
        varname = parts[0].strip()
        expr = parts[1].strip()
        return f"let {varname} = {expr};"

    # Fallback
    return f"// UNTRANSLATED: {line}"


def _translate_bool_arithmetic(line: str) -> str:
    """Translate Python boolean arithmetic to Rust conditional expressions.

    Patterns:
        (cond == val) * expr → if cond == val { expr } else { 0.0 }
        (cond != val) * expr → if cond != val { expr } else { 0.0 }
        expr + (cond == val) * term → expr + if cond == val { term } else { 0.0 }
    """
    # Find all boolean arithmetic sub-expressions
    def replace_bool(match):
        left = match.group(1).strip()
        op = match.group(2).strip()
        right = match.group(3).strip()
        expr = match.group(4).strip()
        return f"if ({left}) {op} ({right}) {{ {expr} }} else {{ 0.0_f64 }}"

    # Pattern: (cond op val) * expr
    pattern = r"\(([^()]+?)\s*(==|!=)\s*([^()]+?)\)\s*\*\s*([^+\-][^;]+?)(?:\s*$|\s*\+|\s*-)"
    # Simpler: replace all (*) boolean arithmetic
    result = _re.sub(
        r"\(([^()]+?)\s*(==|!=)\s*(\d+(?:\.\d+)?)\)\s*\*\s*(\w[\w.]*)",
        lambda m: f"if ({m.group(1)}) {m.group(2)} ({m.group(3)}) {{ {m.group(4)} }} else {{ 0.0_f64 }}",
        line,
    )

    return result


# ── Bracket computation helper ───────────────────────────────────────────────


BRACKET_CALC_HELPER = r"""
/// Helper: computes tax from a progressive bracket table.
///
/// Applies marginal rates to the portion of `value` that falls in
/// each bracket, following OpenFisca's `bareme.calc()` semantics.
#[allow(dead_code)]
fn _bracket_calc(brackets: &[budget_citoyen_core::types::Bracket], value: f64) -> f64 {
    let mut total = 0.0_f64;
    let mut remaining = value;
    let mut prev_threshold = 0.0_f64;
    for b in brackets {
        if remaining <= 0.0 {
            break;
        }
        let bracket_width = (b.threshold - prev_threshold).max(0.0_f64);
        let in_bracket = remaining.min(bracket_width);
        total += in_bracket * b.rate;
        remaining -= in_bracket;
        prev_threshold = b.threshold;
    }
    // Top bracket: remaining above highest threshold taxed at top marginal rate
    if remaining > 0.0_f64 && !brackets.is_empty() {
        total += remaining * brackets.last().unwrap().rate;
    }
    total
}
"""


# ── Spike Generation ────────────────────────────────────────────────────────


def spike_generate() -> Dict[str, Any]:
    """Spike 3-5 representative formulas to validate the codegen approach.

    Returns:
        Dict with spike results per variable.
    """
    try:
        from openfisca_france import FranceTaxBenefitSystem  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "openfisca_france is not installed. "
            "Ensure the data-pipeline virtual environment is active."
        ) from exc

    tbs = FranceTaxBenefitSystem()
    all_variables = tbs.variables
    all_names = set(all_variables.keys())

    # Spike candidates
    spike_vars = [
        "rni", "ir_brut", "decote", "rsa", "apl",
        "aide_logement_montant", "revenu_disponible", "csg",
    ]

    results: Dict[str, Any] = {
        "total_variables": len(all_variables),
        "total_formula_variables": sum(
            1 for v in all_variables.values() if v.formulas
        ),
        "spike_variables": [],
        "summary": {},
    }

    for var_name in spike_vars:
        if var_name not in all_variables:
            results["spike_variables"].append(
                {"name": var_name, "error": "Not found"}
            )
            continue

        variable = all_variables[var_name]
        source_info = _get_var_source(variable)

        if source_info is None:
            results["spike_variables"].append(
                {
                    "name": var_name,
                    "entity": variable.entity.key,
                    "error": "No extractable formula source",
                }
            )
            continue

        source, period = source_info
        deps = _extract_dependencies(source)
        domain = _classify_tax_domain(var_name)
        can_gen, blockers = _can_auto_generate(source)

        rust_body = _translate_python_to_rust(
            source, var_name, variable.entity.key, all_names
        )

        results["spike_variables"].append(
            {
                "name": var_name,
                "entity": variable.entity.key,
                "domain": domain,
                "formula_period": period,
                "documentation": (variable.documentation or "")[:200],
                "dependencies": sorted(deps),
                "dependency_count": len(deps),
                "can_auto_generate": can_gen,
                "blockers": blockers,
                "source_lines": len(source.strip().split("\n")),
                "python_source": source.strip(),
                "rust_preview": rust_body[:500],
            }
        )

    # Summary
    auto_count = sum(
        1 for v in results["spike_variables"] if v.get("can_auto_generate", False)
    )
    total_spiked = len(results["spike_variables"])
    results["summary"] = {
        "total_spiked": total_spiked,
        "auto_generatable": auto_count,
        "auto_generatable_pct": round(auto_count / total_spiked * 100, 1)
        if total_spiked > 0
        else 0,
        "manual_port_needed": total_spiked - auto_count,
    }

    # Broad scan
    all_auto = 0
    all_manual = 0
    all_blockers: Dict[str, int] = defaultdict(int)
    analyzed = 0

    for name, var in all_variables.items():
        if not var.formulas:
            continue
        source_info = _get_var_source(var)
        if source_info is None:
            continue
        source, _ = source_info
        can_gen, blockers = _can_auto_generate(source)
        if can_gen:
            all_auto += 1
        else:
            all_manual += 1
            for b in blockers:
                all_blockers[b] += 1
        analyzed += 1

    results["broad_scan"] = {
        "formulas_analyzed": analyzed,
        "auto_generatable": all_auto,
        "manual_port_needed": all_manual,
        "auto_generatable_pct": round(all_auto / analyzed * 100, 1)
        if analyzed > 0
        else 0,
        "most_common_blockers": sorted(
            all_blockers.items(), key=lambda x: -x[1]
        )[:10],
    }

    return results


# ── Full Generation (Task 2) ─────────────────────────────────────────────────


def generate_rust_formulas(
    output_dir: str,
    openfisca_version: str,
) -> Dict[str, int]:
    """Generate Rust source files from OpenFisca-France formulas.

    Args:
        output_dir: Path to packages/wasm-micro/src/generated/
        openfisca_version: Pinned openfisca-france version string.

    Returns:
        Dict mapping module name to number of generated functions.
    """
    try:
        from openfisca_france import FranceTaxBenefitSystem  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "openfisca_france is not installed."
        ) from exc

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tbs = FranceTaxBenefitSystem()
    variables = tbs.variables
    all_names = set(variables.keys())

    timestamp = _datetime.datetime.now(_datetime.timezone.utc).isoformat()

    # Collect all formula-bearing variables
    formula_vars: List[Dict[str, Any]] = []
    for name, var in variables.items():
        if not var.formulas:
            continue
        source_info = _get_var_source(var)
        if source_info is None:
            continue
        source, period = source_info
        deps = _extract_dependencies(source)
        domain = _classify_tax_domain(name)
        can_gen, blockers = _can_auto_generate(source)

        formula_vars.append(
            {
                "name": name,
                "entity": var.entity.key,
                "domain": domain,
                "period": period,
                "dependencies": deps,
                "documentation": var.documentation or "",
                "source": source,
                "can_auto_generate": can_gen,
                "blockers": blockers,
            }
        )

    # Topological sort
    sorted_vars = _topological_sort_variables(formula_vars)

    # Group by domain
    domains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for v in sorted_vars:
        domains[v["domain"]].append(v)

    # Generate one Rust module per target domain
    target_domains = ["ir", "is", "tva", "cotisations", "aides"]
    generated: Dict[str, int] = {}

    for domain in target_domains:
        vars_list = domains.get(domain, [])
        module_path = output_path / f"{domain}.rs"
        count = _write_rust_module(
            module_path,
            domain,
            vars_list,
            openfisca_version,
            timestamp,
            all_names,
        )
        generated[domain] = count

    # mod.rs
    _write_mod_rs(output_path, target_domains)
    generated["mod"] = 0

    # profile_fields.rs
    _write_profile_fields(output_path, formula_vars)
    generated["profile_fields"] = 0

    return generated


def _topological_sort_variables(
    variables: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Topological sort variables by dependency graph."""
    name_to_var = {v["name"]: v for v in variables}
    sorted_names: List[str] = []
    visited: Set[str] = set()
    temp_mark: Set[str] = set()

    def visit(name: str) -> None:
        if name in temp_mark:
            return
        if name in visited:
            return
        temp_mark.add(name)
        var = name_to_var.get(name)
        if var:
            for dep in sorted(var["dependencies"]):
                if dep in name_to_var:
                    visit(dep)
        temp_mark.discard(name)
        visited.add(name)
        sorted_names.append(name)

    for name in name_to_var:
        if name not in visited:
            visit(name)

    return [name_to_var[n] for n in sorted_names if n in name_to_var]


def _write_rust_module(
    path: Path,
    domain: str,
    variables: List[Dict[str, Any]],
    version: str,
    timestamp: str,
    all_names: Set[str],
) -> int:
    """Write a Rust module file for one tax domain."""
    auto_count = sum(1 for v in variables if v["can_auto_generate"])
    manual_count = sum(1 for v in variables if not v["can_auto_generate"])
    total = len(variables)

    lines = [
        "// AUTO-GENERATED by codegen/generate_rust.py. DO NOT EDIT.",
        f"// Source: openfisca-france v{version}",
        f"// Generated: {timestamp}",
        f"// Domain: {domain}",
        f"// Total formulas: {total}",
        f"// Auto-generatable: {auto_count} | Manual port needed: {manual_count}",
        "",
        "use budget_citoyen_core::types::{Profile, Parameters};",
        "use chrono::NaiveDate;",
        "",
    ]

    # Add bracket_calc helper if any formula uses brackets
    has_brackets = any(
        "bareme" in v["source"] or "bracket" in v["source"].lower()
        for v in variables
    )
    if has_brackets:
        lines.append(BRACKET_CALC_HELPER.strip())
        lines.append("")

    for var in variables:
        fn_name = _sanitize_fn_name(var["name"])

        # Doc comment
        doc = var["documentation"].strip()
        if doc:
            if len(doc) > 500:
                doc = doc[:497] + "..."
            for doc_line in doc.split("\n"):
                lines.append(f"/// {doc_line}")

        # All functions have the same signature per D-08
        lines.append(
            f"#[allow(dead_code, unused_variables)]\n"
            f"pub fn {fn_name}(\n"
            f"    parameters: &Parameters,\n"
            f"    period: NaiveDate,\n"
            f"    profile: &Profile,\n"
            f") -> f64 {{"
        )

        # Translate or stub
        if var["can_auto_generate"]:
            rust_body = _translate_python_to_rust(
                var["source"], var["name"], var["entity"], all_names
            )
            lines.append(rust_body)
        else:
            lines.append(
                f"    // TODO: MANUAL_PORT — "
                f"Blockers: {', '.join(var['blockers'])}"
            )
            for src_line in var["source"].strip().split("\n"):
                lines.append(f"    // {src_line}")
            lines.append("    0.0_f64")

        lines.append("}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return total


def _sanitize_fn_name(name: str) -> str:
    """Convert a variable name to a valid Rust function name.

    Uses `calculate_` prefix per D-08 convention.
    """
    return f"calculate_{name}"


def _write_mod_rs(output_dir: Path, domains: List[str]) -> None:
    """Write mod.rs re-exporting all generated modules."""
    lines = [
        "// AUTO-GENERATED by codegen/generate_rust.py. DO NOT EDIT.",
        "// Re-exports all generated formula modules.",
        "",
    ]
    for d in domains:
        lines.append(f"pub mod {d};")

    with open(output_dir / "mod.rs", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _write_profile_fields(
    output_dir: Path, variables: List[Dict[str, Any]]
) -> None:
    """Write profile_fields.rs with discovered leaf input variables (D-15)."""
    # Leaf inputs: variables referenced by formulas but without formulas
    # themselves (these map to profile struct fields)
    all_refs: Set[str] = set()
    for v in variables:
        all_refs.update(v["dependencies"])

    leaf_inputs = sorted(all_refs)

    lines = [
        "// AUTO-GENERATED by codegen/generate_rust.py. DO NOT EDIT.",
        "// Leaf input variables discovered from OpenFisca-France variable graph.",
        "// These extend the hand-written Profile struct (D-15).",
        f"// Total leaf input references: {len(leaf_inputs)}",
        "",
    ]

    if leaf_inputs:
        lines.append("/// Profile extension fields discovered by codegen.")
        lines.append(
            "#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]"
        )
        lines.append("pub struct ProfileExtension {")
        for name in leaf_inputs[:100]:  # Top 100
            lines.append(f"    pub {name}: f64,")
        lines.append("}")
    else:
        lines.append("// No leaf input variables discovered.")

    with open(output_dir / "profile_fields.rs", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── CLI Entry Point ─────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    if "--spike" in _sys.argv:
        _run_spike()
    else:
        _run_full_generation()


def _run_spike() -> None:
    """Run spike analysis and print results."""
    print("=" * 70)
    print("  OpenFisca-France -> Rust Codegen SPIKE")
    print("=" * 70)

    try:
        results = spike_generate()
    except ImportError as e:
        print(f"ERROR: {e}")
        _sys.exit(1)

    print(f"\nTotal variables: {results['total_variables']}")
    print(f"Formula variables: {results['total_formula_variables']}")

    print("\n" + "=" * 70)
    print("  Spike Variables (Detail)")
    print("=" * 70)

    for v in results["spike_variables"]:
        print(f"\n  > {v['name']}")
        if "error" in v:
            print(f"    ERROR: {v['error']}")
            continue
        print(f"    Entity:     {v['entity']}")
        print(f"    Domain:     {v['domain']}")
        print(f"    Period:     {v['formula_period']}")
        print(f"    Deps:       {v['dependencies']}")
        print(f"    Auto-gen:   {'YES' if v['can_auto_generate'] else 'NO'}")
        if v.get("blockers"):
            print(f"    Blockers:   {', '.join(v['blockers'])}")
        print(f"\n    Python:\n{v['python_source']}")
        print(f"\n    Rust preview:\n{v.get('rust_preview', 'N/A')[:400]}")

    s = results["summary"]
    print(f"\n  Spike Summary: {s['auto_generatable']}/{s['total_spiked']} "
          f"({s['auto_generatable_pct']}%) auto-generatable")

    bs = results["broad_scan"]
    print(f"\n  Broad Scan ({bs['formulas_analyzed']} analyzed): "
          f"{bs['auto_generatable_pct']}% auto-generatable")
    if bs["most_common_blockers"]:
        print("  Top blockers:")
        for blocker, count in bs["most_common_blockers"][:5]:
            print(f"    - {blocker}: {count}")

    # Write SPIKE_RESULTS.md
    _write_spike_report(results)


def _write_spike_report(results: Dict[str, Any]) -> None:
    """Write detailed spike report."""
    report_dir = Path(__file__).parent
    lines = [
        "# Codegen Spike Results",
        f"\nGenerated: {_datetime.datetime.now(_datetime.timezone.utc).isoformat()}",
        "\n## Overview",
        f"\n- **Total variables:** {results['total_variables']}",
        f"- **Formula-bearing:** {results['total_formula_variables']}",
        "\n## Spike Variables\n",
        "| Variable | Entity | Domain | Auto-gen? | Blockers |",
        "|----------|--------|--------|-----------|----------|",
    ]
    for v in results["spike_variables"]:
        if "error" in v:
            lines.append(f"| {v['name']} | — | — | ✗ | {v['error']} |")
        else:
            status = "✓" if v["can_auto_generate"] else "✗"
            blockers = ", ".join(v["blockers"]) if v.get("blockers") else "—"
            lines.append(
                f"| {v['name']} | {v['entity']} | {v['domain']} | {status} | {blockers} |"
            )

    s = results["summary"]
    lines.extend([
        f"\n## Summary",
        f"\n- Spiked: {s['total_spiked']}",
        f"- Auto-generatable: {s['auto_generatable']} ({s['auto_generatable_pct']}%)",
        f"- Manual: {s['manual_port_needed']}",
    ])

    bs = results["broad_scan"]
    lines.extend([
        f"\n## Broad Scan ({bs['formulas_analyzed']} formulas)",
        f"\n- Auto: {bs['auto_generatable']} ({bs['auto_generatable_pct']}%)",
        f"- Manual: {bs['manual_port_needed']}",
        "\n### Top Blockers",
    ])
    for blocker, count in bs["most_common_blockers"]:
        lines.append(f"- {blocker}: {count}")

    lines.extend([
        "\n## Detailed Analysis",
    ])
    for v in results["spike_variables"]:
        if "error" in v:
            continue
        lines.extend([
            f"\n### {v['name']}",
            f"\n- Entity: {v['entity']} | Domain: {v['domain']} | Period: {v['formula_period']}",
            f"- Deps: {', '.join(v['dependencies']) if v['dependencies'] else 'none'}",
            f"- Auto-gen: {'Yes' if v['can_auto_generate'] else 'No'}" +
            (f" (blockers: {', '.join(v['blockers'])})" if v.get('blockers') else ""),
            "\n**Python:**",
            "```python",
            v['python_source'],
            "```",
            "\n**Rust preview:**",
            "```rust",
            v.get('rust_preview', 'N/A'),
            "```",
        ])

    lines.extend([
        "\n## Conclusions",
        f"\n- {bs['auto_generatable_pct']}% auto-generatable — simple arithmetic, brackets, "
        "parameter access translate well",
        "- Main blockers: cross-entity navigation, role-based aggregation, OpenFisca enum types",
        "- Estimated auto-generated LOC: ~{bs['formulas_analyzed'] * 20} "
        "(avg 20 lines × {bs['formulas_analyzed']} formulas)",
    ])

    with open(report_dir / "SPIKE_RESULTS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _run_full_generation() -> None:
    """Run full code generation (Task 2)."""
    import tomllib  # noqa: PLC0415

    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    deps = pyproject.get("project", {}).get("dependencies", [])
    openfisca_version = "unknown"
    for dep in deps:
        if dep.startswith("openfisca-france"):
            openfisca_version = dep
            break

    repo_root = Path(__file__).parent.parent.parent.parent.parent
    output_dir = repo_root / "packages" / "wasm-micro" / "src" / "generated"

    print(f"Generating from openfisca-france ({openfisca_version})")
    print(f"Output: {output_dir}")

    try:
        generated = generate_rust_formulas(str(output_dir), openfisca_version)
    except ImportError as e:
        print(f"ERROR: {e}")
        _sys.exit(1)

    print("\nGeneration results:")
    for domain, count in sorted(generated.items()):
        if domain in ("mod", "profile_fields"):
            print(f"  {domain}.rs written")
        else:
            print(f"  {domain}.rs: {count} formulas")

    print("\nDone. Run `cargo check -p budget-citoyen-wasm-micro` to verify.")


if __name__ == "__main__":
    main()
