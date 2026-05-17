"""Validateur V1.81.9 – Smoke ultra-borné, alignement strict, couverture > 100, anti-tautologie."""
from pathlib import Path
import sys
import argparse
import json
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import (
    version_to_suffix,
    parse_version,
)

APPROVAL_PHRASE = (
    "J'approuve V1.82 dry-run data contract reports-only, "
    "sans écriture data, sans dataset, sans trading."
)

REQUIRED_RESEARCH_REPORTS_V1_81_9 = [
    "microstructure_data_contract_approval_intake_corrective_summary_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_summary_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_safety_check_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_safety_check_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_negative_coverage_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_negative_coverage_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_test_quality_audit_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_test_quality_audit_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_anti_tautology_audit_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_anti_tautology_audit_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_smoke_state_alignment_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_smoke_state_alignment_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_script_portability_audit_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_script_portability_audit_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_release_metadata_audit_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_release_metadata_audit_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_current_state_alignment_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_current_state_alignment_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_release_packaging_audit_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_release_packaging_audit_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_decision_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_decision_v1_81_9.md",
    "microstructure_data_contract_approval_intake_corrective_consistency_check_v1_81_9.json",
    "microstructure_data_contract_approval_intake_corrective_consistency_check_v1_81_9.md",
    "v1_81_9_recommendation.json",
    "v1_81_9_recommendation.md",
]

REQUIRED_ROOT_REPORTS_V1_81_9 = [
    "release_zip_v1_81_9.json",
    "release_zip_v1_81_9.md",
    "zip_audit_v1_81_9.json",
    "zip_audit_v1_81_9.md",
    "zip_smoke_test_v1_81_9.json",
    "zip_smoke_test_v1_81_9.md",
]

REQUIRED_DOCS_V1_81_9 = [
    "microstructure_data_contract_approval_intake_corrective_v1_81_9.md",
    "code_review_v1_81_9.md",
]

def _script_has_bootstrap(script_path: Path) -> bool:
    if not script_path.exists(): return False
    content = script_path.read_text()
    return "sys.path.insert" in content and ("PROJECT_ROOT" in content or "parents[1]" in content or "parents[2]" in content)

def main() -> None:
    parser = argparse.ArgumentParser(description="Validateur V1.81.9")
    parser.add_argument("--version", default="v1_81_9")
    args = parser.parse_args()

    v_disp = parse_version(args.version)
    v_suffix = version_to_suffix(args.version)
    errors: list[str] = []
    
    reports_dir = PROJECT_ROOT / "reports"
    research_dir = reports_dir / "research"
    docs_dir = PROJECT_ROOT / "docs"

    # 1. CLI Contract
    run_script = PROJECT_ROOT / f"scripts/run_microstructure_data_contract_approval_intake_corrective_{v_suffix}.py"
    if run_script.exists():
        content = run_script.read_text()
        if "--approval-phrase" not in content:
            errors.append(f"FAILED_RUN_CLI_CONTRACT: {run_script.name} manque --approval-phrase")

    # 2. Portabilité
    for s in [run_script, PROJECT_ROOT / f"scripts/validate_microstructure_data_contract_approval_intake_corrective_{v_suffix}_reports.py"]:
        if s.exists() and not _script_has_bootstrap(s):
            errors.append(f"FAILED_SCRIPT_IMPORT_PORTABILITY: {s.name} bootstrap manquant")

    # 3. Rapports obligatoires
    for fname in REQUIRED_RESEARCH_REPORTS_V1_81_9:
        if not (research_dir / fname).exists(): errors.append(f"MISSING_RESEARCH_REPORT: {fname}")
    for fname in REQUIRED_ROOT_REPORTS_V1_81_9:
        if not (reports_dir / fname).exists(): errors.append(f"MISSING_ROOT_REPORT: {fname}")
    for fname in REQUIRED_DOCS_V1_81_9:
        if not (docs_dir / fname).exists(): errors.append(f"MISSING_DOC: {fname}")

    # 4. REPORT_INDEX
    report_index = reports_dir / "REPORT_INDEX.md"
    if report_index.exists():
        content = report_index.read_text()
        if "V1.81.9" not in content: errors.append("FAILED_REPORT_INDEX: Référence V1.81.9 manquante")

    # 5. Alignement Smoke / State / Summary
    smoke_f = reports_dir / f"zip_smoke_test_{v_suffix}.json"
    state_f = reports_dir / "PROJECT_STATE.json"
    summary_f = research_dir / f"microstructure_data_contract_approval_intake_corrective_summary_{v_suffix}.json"
    ata_f = research_dir / f"microstructure_data_contract_approval_intake_corrective_anti_tautology_audit_{v_suffix}.json"

    if smoke_f.exists() and state_f.exists() and summary_f.exists():
        with open(smoke_f) as f: smoke = json.load(f)
        with open(state_f) as f: state = json.load(f)
        with open(summary_f) as f: summary = json.load(f)

        s_passed = smoke.get("smoke_test_passed", False)
        s_timeout = smoke.get("smoke_timeout_detected", True)
        s_heavy = (smoke.get("smoke_runs_audit_clean_zip_full_scan", True) or 
                   smoke.get("smoke_runs_full_v1_81_9_pytest_suite", True))

        if not s_passed or s_timeout or s_heavy:
            errors.append(f"VALIDATOR_REJECTS_INVALID_SMOKE_STATE: passed={s_passed}, timeout={s_timeout}, heavy={s_heavy}")

        if s_passed != state.get("smoke_test_passed") or s_passed != summary.get("smoke_test_passed"):
            errors.append("VALIDATOR_REJECTS_SMOKE_ALIGNMENT_MISMATCH: smoke_test_passed incohérent")

    # 6. Anti-Tautologie et Couverture
    if ata_f.exists():
        with open(ata_f) as f: ata = json.load(f)
        if ata.get("tautological_tests_count", 0) > 0:
            errors.append(f"VALIDATOR_REJECTS_TAUTOLOGIES: {ata.get('tautological_tests')}")

    # Vérification couverture tests dans summary
    if summary_f.exists():
        with open(summary_f) as f: summary = json.load(f)
        test_count = summary.get("total_tests_executed", 0)
        if test_count < 100:
            errors.append(f"VALIDATOR_REJECTS_LOW_TEST_COVERAGE: {test_count} tests (attendu >= 100)")

    if errors:
        print(f"ERROR: Validation V1.81.9 échouée ({len(errors)}):")
        for e in errors: print(f"  - {e}")
        sys.exit(1)

    print("SUCCESS: V1.81.9 VALIDATED.")

if __name__ == "__main__":
    main()
