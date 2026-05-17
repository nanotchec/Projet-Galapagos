"""Validateur V1.81.7 – vérifie CLI, imports, rapports canoniques, REPORT_INDEX et smoke sans PYTHONPATH."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import argparse
import ast
import json
import re
import subprocess

from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import (
    version_to_suffix,
    parse_version,
)

APPROVAL_PHRASE = (
    "J'approuve V1.82 dry-run data contract reports-only, "
    "sans écriture data, sans dataset, sans trading."
)

# Rapports canoniques obligatoires dans reports/research/
REQUIRED_RESEARCH_REPORTS_V1_81_7 = [
    "microstructure_data_contract_approval_intake_corrective_summary_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_summary_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_safety_check_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_safety_check_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_negative_coverage_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_negative_coverage_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_test_quality_audit_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_test_quality_audit_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_script_portability_audit_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_script_portability_audit_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_release_metadata_audit_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_release_metadata_audit_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_current_state_alignment_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_current_state_alignment_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_release_packaging_audit_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_release_packaging_audit_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_decision_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_decision_v1_81_7.md",
    "microstructure_data_contract_approval_intake_corrective_consistency_check_v1_81_7.json",
    "microstructure_data_contract_approval_intake_corrective_consistency_check_v1_81_7.md",
    "v1_81_7_recommendation.json",
    "v1_81_7_recommendation.md",
]

REQUIRED_ROOT_REPORTS_V1_81_7 = [
    "release_zip_v1_81_7.json",
    "release_zip_v1_81_7.md",
    "zip_audit_v1_81_7.json",
    "zip_audit_v1_81_7.md",
    "zip_smoke_test_v1_81_7.json",
    "zip_smoke_test_v1_81_7.md",
]

REQUIRED_DOCS_V1_81_7 = [
    "microstructure_data_contract_approval_intake_corrective_v1_81_7.md",
    "code_review_v1_81_7.md",
]


def _script_has_bootstrap(script_path: Path) -> bool:
    """Vérifie qu'un script Python contient l'injection sys.path correcte."""
    if not script_path.exists():
        return False
    content = script_path.read_text()
    return "sys.path.insert" in content and ("PROJECT_ROOT" in content or "parents[1]" in content or "parents[2]" in content)


def _script_has_approval_phrase_arg(script_path: Path) -> bool:
    """Vérifie que le script run accepte --approval-phrase."""
    if not script_path.exists():
        return False
    content = script_path.read_text()
    return "--approval-phrase" in content or "approval_phrase" in content or "approval-phrase" in content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validateur rapports V1.81.7"
    )
    parser.add_argument("--version", default="v1_81_7")
    args = parser.parse_args()

    v_disp = parse_version(args.version)
    v_suffix = version_to_suffix(args.version)

    errors: list[str] = []
    reports_dir = PROJECT_ROOT / "reports"
    research_dir = reports_dir / "research"
    docs_dir = PROJECT_ROOT / "docs"

    # ── 1. CLI Contract : --approval-phrase ──────────────────────────────────
    run_script = PROJECT_ROOT / f"scripts/run_microstructure_data_contract_approval_intake_corrective_{v_suffix}.py"
    if not _script_has_approval_phrase_arg(run_script):
        errors.append(f"FAILED_RUN_CLI_CONTRACT: {run_script.name} ne supporte pas --approval-phrase")

    # ── 2. Portabilité sans PYTHONPATH ───────────────────────────────────────
    scripts_to_check = [
        run_script,
        PROJECT_ROOT / f"scripts/validate_microstructure_data_contract_approval_intake_corrective_{v_suffix}_reports.py",
    ]
    for s in scripts_to_check:
        if s.exists() and not _script_has_bootstrap(s):
            errors.append(f"FAILED_SCRIPT_IMPORT_PORTABILITY: {s.name} manque le bootstrap sys.path")

    # ── 3. Rapports obligatoires dans reports/research/ ──────────────────────
    missing_research = []
    for fname in REQUIRED_RESEARCH_REPORTS_V1_81_7:
        if not (research_dir / fname).exists():
            missing_research.append(f"reports/research/{fname}")
    if missing_research:
        errors.append(f"FAILED_MISSING_REQUIRED_RESEARCH_REPORTS: {missing_research}")

    # ── 4. Rapports root-level ────────────────────────────────────────────────
    missing_root = []
    for fname in REQUIRED_ROOT_REPORTS_V1_81_7:
        if not (reports_dir / fname).exists():
            missing_root.append(f"reports/{fname}")
    if missing_root:
        errors.append(f"FAILED_MISSING_REQUIRED_ROOT_REPORTS: {missing_root}")

    # ── 5. docs/code_review_v1_81_7.md ───────────────────────────────────────
    missing_docs = []
    for dname in REQUIRED_DOCS_V1_81_7:
        if not (docs_dir / dname).exists():
            missing_docs.append(f"docs/{dname}")
    if missing_docs:
        errors.append(f"FAILED_MISSING_REQUIRED_DOCS: {missing_docs}")

    # ── 6. REPORT_INDEX références canoniques ────────────────────────────────
    report_index = reports_dir / "REPORT_INDEX.md"
    if report_index.exists():
        content = report_index.read_text()
        if v_suffix not in content:
            errors.append("FAILED_REPORT_INDEX_BROKEN_OR_NON_CANONICAL: REPORT_INDEX ne référence pas v1_81_7")

        # Extraire uniquement la section V1.81.7 du REPORT_INDEX
        v1_81_7_section = ""
        in_section = False
        for line in content.splitlines():
            if f"[V1.81.7]" in line or f"v1_81_7" in line.lower() and line.startswith("#"):
                in_section = True
            elif line.startswith("## [") and "V1.81.7" not in line:
                in_section = False
            if in_section:
                v1_81_7_section += line + "\n"

        # Vérifier les liens uniquement dans la section V1.81.7
        broken = []
        v1_81_7_links = re.findall(r"\[.*?\]\((.*?)\)", v1_81_7_section)
        for link in v1_81_7_links:
            if link.startswith("http"):
                continue
            target = report_index.parent / link
            if not target.exists():
                broken.append(link)
        if broken:
            errors.append(f"FAILED_REPORT_INDEX_BROKEN_OR_NON_CANONICAL: liens brisés dans section V1.81.7 = {broken}")
    else:
        errors.append("FAILED_REPORT_INDEX_BROKEN_OR_NON_CANONICAL: REPORT_INDEX.md absent")

    # ── 7. Alignment final ───────────────────────────────────────────────────
    state_path = reports_dir / "PROJECT_STATE.json"
    if state_path.exists():
        data = json.loads(state_path.read_text())
        if data.get("version") != v_disp:
            errors.append(f"Version mismatch PROJECT_STATE: attendu {v_disp}, trouvé {data.get('version')}")
        expected_verdict = "V1_81_7_CLI_IMPORT_REPORTS_AND_SMOKE_HARDENING_PASSED"
        if data.get("final_verdict") != expected_verdict:
            errors.append(f"Verdict mismatch: attendu {expected_verdict}, trouvé {data.get('final_verdict')}")
        if not data.get("test_quality_passed"):
            errors.append("Test quality audit failed in PROJECT_STATE")

    if errors:
        print(f"ERROR: Validation {v_disp} échouée avec {len(errors)} problème(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"SUCCESS: Tous les rapports V1.81.7 validés pour {v_disp}")


if __name__ == "__main__":
    main()
