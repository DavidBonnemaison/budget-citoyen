"""Check if pinned openfisca-france version is stale vs PyPI latest.

Compares the pinned version constraint in pyproject.toml against the
latest release on PyPI. Emits a GitHub Actions warning annotation
(soft gate per D-07 — never a hard failure).

CI integration (Plan 02-08):
  Add a `version-check` job to `.github/workflows/phase2-wasm.yml`:
    - Runs on ubuntu-latest, Python 3.10
    - Installs dependencies from packages/data-pipeline/pyproject.toml
    - Runs: cd packages/data-pipeline && PYTHONPATH=src python -m codegen.check_staleness
    - Always exits 0 (soft warning per D-07)
    - When stale: re-run codegen (`python -m codegen.generate_rust`) and commit

Usage:
  python -m codegen.check_staleness        # CI mode (GitHub Actions warnings)
  python -m codegen.check_staleness --json # Machine-readable JSON output

Exit codes:
  0 — Always (D-07: CI step emits a soft warning, not hard gate)
"""

import json as _json
import re as _re
import sys as _sys
import tomllib as _tomllib
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import Request, urlopen


# ── Version parsing ──────────────────────────────────────────────────────────


def _parse_version_constraint(
    constraint: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Parse a PEP 508 version constraint into (lower_bound, upper_bound).

    Args:
        constraint: Version constraint string (e.g., ">=159,<200").

    Returns:
        Tuple of (lower_version, upper_version). Either may be None.
    """
    lower = None
    upper = None

    # Match: >=159
    lower_match = _re.search(r">=\s*([\d.]+)", constraint)
    if lower_match:
        lower = lower_match.group(1)

    # Match: <200 or <=199
    upper_match = _re.search(r"<\s*=?\s*([\d.]+)", constraint)
    if upper_match:
        upper = upper_match.group(1)

    return lower, upper


def _get_pinned_version() -> Tuple[str, str]:
    """Extract the pinned openfisca-france version from pyproject.toml.

    Returns:
        Tuple of (version_constraint_string, dep_line).
    """
    pyproject_path = (
        Path(__file__).parent.parent.parent / "pyproject.toml"
    )

    with open(pyproject_path, "rb") as f:
        pyproject = _tomllib.load(f)

    deps = pyproject.get("project", {}).get("dependencies", [])
    for dep in deps:
        if dep.startswith("openfisca-france"):
            return dep, dep.split("openfisca-france", 1)[1].strip()

    raise ValueError(
        "openfisca-france dependency not found in pyproject.toml"
    )


# ── PyPI API ─────────────────────────────────────────────────────────────────


def _get_latest_pypi_version(package_name: str = "openfisca-france") -> str:
    """Query PyPI JSON API for the latest version of a package.

    Args:
        package_name: The PyPI package name.

    Returns:
        Latest version string (e.g., "159.0.0").

    Raises:
        RuntimeError: If the PyPI API is unreachable.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(req, timeout=30) as response:
            data = _json.loads(response.read().decode())
    except Exception as exc:
        raise RuntimeError(
            f"Failed to query PyPI API for {package_name}: {exc}"
        ) from exc

    return data["info"]["version"]


# ── Version comparison ──────────────────────────────────────────────────────


def _version_tuple(version_str: str) -> Tuple[int, ...]:
    """Parse a version string into a comparable tuple."""
    parts = version_str.split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def _is_stale(
    pinned_upper: Optional[str], latest: str
) -> Tuple[bool, str]:
    """Check if the latest version exceeds the pinned upper bound.

    Args:
        pinned_upper: Upper bound of pinned constraint, or None.
        latest: Latest version from PyPI.

    Returns:
        Tuple of (is_stale, reason_string).
    """
    if pinned_upper is None:
        return False, "No upper bound specified — open range"

    pinned_tuple = _version_tuple(pinned_upper)
    latest_tuple = _version_tuple(latest)

    if latest_tuple > pinned_tuple:
        return True, (
            f"Latest version {latest} exceeds pinned upper bound "
            f"<{pinned_upper}"
        )
    return False, (
        f"Latest version {latest} is within pinned range "
        f"(upper bound <{pinned_upper})"
    )


# ── Output formatting ────────────────────────────────────────────────────────


def _emit_github_warning(
    pinned_constraint: str,
    latest_version: str,
    pinned_upper: Optional[str],
    reason: str,
) -> None:
    """Emit a GitHub Actions warning annotation.

    Per D-07: This is a soft warning — never a hard gate.
    The annotation points to pyproject.toml for inline display in PRs.
    """
    pyproject_rel = "packages/data-pipeline/pyproject.toml"
    message = (
        f"OpenFisca-France is stale: pinned {pinned_constraint}, "
        f"latest {latest_version}. "
        "Re-run codegen: cd packages/data-pipeline && "
        "PYTHONPATH=src python -m codegen.generate_rust"
    )
    print(
        f"::warning file={pyproject_rel},line=1,"
        f"title=OpenFisca-France Staleness::{message}"
    )


def _emit_json_output(
    pinned_constraint: str,
    pinned_upper: Optional[str],
    latest_version: str,
    is_stale: bool,
    reason: str,
) -> None:
    """Emit machine-readable JSON output."""
    output = {
        "package": "openfisca-france",
        "pinned_constraint": pinned_constraint,
        "pinned_upper_bound": pinned_upper,
        "latest_version": latest_version,
        "is_stale": is_stale,
        "reason": reason,
        "action": (
            "Re-run codegen: PYTHONPATH=src python -m codegen.generate_rust"
            if is_stale
            else None
        ),
    }
    print(_json.dumps(output, indent=2))


# ── Main entry point ─────────────────────────────────────────────────────────


def check_staleness() -> bool:
    """Run the staleness check and return whether upstream is stale.

    Returns:
        True if upstream is newer than pinned, False otherwise.

    Note: Always exits 0 per D-07 — CI step emits a soft warning, not hard gate.
    """
    try:
        pinned_constraint, _ = _get_pinned_version()
    except ValueError as exc:
        print(f"::warning file=packages/data-pipeline/pyproject.toml,"
              f"line=1,title=OpenFisca-France Staleness::"
              f"Cannot parse version: {exc}")
        return False

    _, pinned_upper = _parse_version_constraint(pinned_constraint)

    try:
        latest_version = _get_latest_pypi_version("openfisca-france")
    except RuntimeError as exc:
        # Network issue — don't block CI
        print(
            f"::warning file=packages/data-pipeline/pyproject.toml,"
            f"line=1,title=OpenFisca-France Staleness::"
            f"Cannot check PyPI: {exc}"
        )
        return False

    stale, reason = _is_stale(pinned_upper, latest_version)

    if _sys.argv[-1] == "--json":
        _emit_json_output(
            pinned_constraint, pinned_upper, latest_version, stale, reason
        )
    else:
        print(f"Pinned constraint: {pinned_constraint}")
        print(f"Latest PyPI:       {latest_version}")
        print(f"Status:            {'STALE — re-run codegen' if stale else 'Up to date'}")
        print(f"Reason:            {reason}")

        if stale:
            _emit_github_warning(
                pinned_constraint, latest_version, pinned_upper, reason
            )

    return stale


def main() -> None:
    """CLI entry point."""
    is_stale = check_staleness()

    # Per D-07: always exit 0 — soft warning, never hard gate
    if is_stale:
        print(
            "\n[SOFT WARNING] Upstream openfisca-france has a newer version. "
            "Re-run codegen when convenient.",
            file=_sys.stderr,
        )

    _sys.exit(0)


if __name__ == "__main__":
    main()
