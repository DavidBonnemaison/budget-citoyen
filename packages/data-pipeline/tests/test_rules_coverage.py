"""Tests for tax rules YAML parameter file coverage and integrity.

Validates:
- DATA-01: At least 31 YAML parameter files exist across 5 domains
- DATA-01: credits.yaml has 25+ tax credit entries
- DATA-01: Domain index.yaml files reference complete file inventories
"""

import sys
from pathlib import Path

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

TAX_RULES_PARAMETERS = (
    Path(__file__).resolve().parent.parent.parent / "tax-rules" / "parameters"
)
DOMAINS = ["ir", "is", "tva", "cotisations", "aides"]


class TestYamlParameterFileCount:
    """Gap 1 — DATA-01: YAML parameter file count verification.

    Requirement: "31 YAML parameter files across 5 domains exist"
    (from 01-GAP-CLOSURE-SUMMARY).
    """

    def test_at_least_31_parameter_files_across_5_domains(self):
        """Count .yaml files in each domain, excluding index.yaml.

        Counts only non-index YAML files as they represent actual
        parameter definitions. Index files are metadata, not parameters.
        """
        total = 0
        counts = {}
        for domain in DOMAINS:
            domain_dir = TAX_RULES_PARAMETERS / domain
            if not domain_dir.is_dir():
                continue
            yaml_files = sorted(domain_dir.glob("*.yaml"))
            param_files = [f for f in yaml_files if f.name != "index.yaml"]
            counts[domain] = len(param_files)
            total += len(param_files)

        assert total >= 31, (
            f"Expected >= 31 YAML parameter files across 5 domains, "
            f"found {total}. Per-domain counts: {counts}"
        )

    def test_all_5_domains_have_parameter_files(self):
        """Every domain directory has at least one non-index YAML file."""
        for domain in DOMAINS:
            domain_dir = TAX_RULES_PARAMETERS / domain
            assert domain_dir.is_dir(), f"Missing domain directory: {domain}"
            yaml_files = sorted(domain_dir.glob("*.yaml"))
            param_files = [f for f in yaml_files if f.name != "index.yaml"]
            assert len(param_files) > 0, (
                f"Domain '{domain}' has no parameter YAML files "
                f"(only index.yaml or empty)"
            )


class TestCreditsYamlEntries:
    """Gap 2 — DATA-01: credits.yaml contains 25+ tax credit entries.

    Requirement: "credits.yaml contains 25+ tax credit entries"
    (from 01-GAP-CLOSURE-SUMMARY).
    """

    def test_credits_yaml_has_25_plus_entries(self):
        """Load credits.yaml and count distinct tax credit entries.

        PyYAML parses '2025-01-01' as datetime.date, so we must
        iterate values dict keys to find entries regardless of key type.
        """
        import yaml

        credits_path = TAX_RULES_PARAMETERS / "ir" / "credits.yaml"
        assert credits_path.exists(), f"credits.yaml not found at {credits_path}"

        with open(credits_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Navigate: data.values -> {datetime.date(2025,1,1): {value: {...}}}
        values = data.get("values", {})
        # Iterate all date-keyed entries (may be datetime.date objects)
        entry_count = 0
        entry_names = []
        for date_key, date_value in values.items():
            inner_value = date_value.get("value", {})
            if isinstance(inner_value, dict):
                entry_count = len(inner_value)
                entry_names = sorted(inner_value.keys())

        assert entry_count >= 25, (
            f"credits.yaml has {entry_count} entries, expected >= 25. "
            f"Entries found: {entry_names if entry_count < 30 else f'{entry_count} total'}"
        )

    def test_credits_entries_have_legislation_references(self):
        """Every tax credit entry in credits.yaml has a legifrance reference."""
        import yaml

        credits_path = TAX_RULES_PARAMETERS / "ir" / "credits.yaml"

        with open(credits_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        values = data.get("values", {})
        missing_refs = []
        for date_key, date_value in values.items():
            inner_value = date_value.get("value", {})
            if isinstance(inner_value, dict):
                for entry_name, entry_data in inner_value.items():
                    if isinstance(entry_data, dict):
                        ref = entry_data.get("reference", "")
                        if not ref or "legifrance" not in ref:
                            missing_refs.append(entry_name)

        assert len(missing_refs) == 0, (
            f"Entries missing legifrance.gouv.fr references: {missing_refs}"
        )


class TestDomainIndexConsistency:
    """Gap 4 — DATA-01: Domain index.yaml file consistency.

    Requirement: "All 5 domain index.yaml files reference their complete
    parameter file inventories" (from 01-GAP-CLOSURE-PLAN must_haves).
    """

    def test_index_references_all_existing_yaml_files(self):
        """For each domain, every non-index .yaml listed in index exists on disk."""
        import yaml

        issues = []
        for domain in DOMAINS:
            domain_dir = TAX_RULES_PARAMETERS / domain
            index_path = domain_dir / "index.yaml"
            if not index_path.exists():
                issues.append(f"{domain}: index.yaml missing")
                continue

            with open(index_path, encoding="utf-8") as f:
                index_data = yaml.safe_load(f)

            # Get list of parameter filenames referenced in index
            # Index format: parameters: [{file: xxx.yaml, ...}, ...]
            params = index_data.get("parameters", [])
            referenced_files = set()
            for p in params:
                if isinstance(p, dict) and "file" in p:
                    referenced_files.add(p["file"])

            # Get actual non-index .yaml files on disk
            actual_files = {
                f.name for f in domain_dir.glob("*.yaml")
                if f.name != "index.yaml"
            }

            # Every referenced file must exist on disk
            missing = referenced_files - actual_files
            if missing:
                issues.append(
                    f"{domain}: index references files not on disk: {missing}"
                )

            # Every actual file should be referenced in index
            unreferenced = actual_files - referenced_files
            if unreferenced:
                issues.append(
                    f"{domain}: files on disk not in index: {unreferenced}"
                )

        assert len(issues) == 0, (
            f"Domain index consistency issues:\n" +
            "\n".join(f"  - {i}" for i in issues)
        )

    def test_all_5_domain_indexes_exist(self):
        """Every domain has an index.yaml file."""
        for domain in DOMAINS:
            index_path = TAX_RULES_PARAMETERS / domain / "index.yaml"
            assert index_path.exists(), (
                f"Missing index.yaml for domain '{domain}'"
            )
