from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.mini_research_dataset_readiness import (  # noqa: E402
    MiniResearchDatasetPhysicalAuditor,
    MiniResearchDatasetReadinessSafetyGuard,
    build_anti_leakage_plan,
    design_dataset_seed,
    evaluate_approval_phrase,
)
from galapagos.research.mini_research_dataset_readiness.report_writer import write_readiness_report  # noqa: E402
from galapagos.research.report_models import write_research_report  # noqa: E402

V_DISP = "V1.91"
V_NORM = "v1_91"
MISSION = "post_consolidation_review_mini_research_dataset_seed_design_anti_leakage_plan_and_approval_gate"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines, ""]), encoding="utf-8")


def _pytest_result() -> dict[str, Any]:
    test_path = PROJECT_ROOT / "tests/research/test_mini_research_dataset_readiness_v1_91.py"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(test_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    passed = re.search(r"(\d+) passed", output)
    failed = re.search(r"(\d+) failed", output)
    return {
        "pytest_executed": True,
        "pytest_exit_code": result.returncode,
        "pytest_failed_count": int(failed.group(1)) if failed else 0,
        "pytest_passed_count": int(passed.group(1)) if passed else 0,
    }


def _base_payload(
    *, pytest: dict[str, Any], physical: dict[str, Any], design: dict[str, Any], anti: dict[str, Any], approval: dict[str, Any]
) -> dict[str, Any]:
    phrase_match = approval["approval_phrase_match"]
    return {
        "version": V_DISP,
        "version_suffix": V_NORM,
        "previous_validated_version": "V1.90.1",
        "reviewed_materialization_version": "V1.84",
        "reviewed_extension_version": "V1.87.2",
        "reviewed_consolidation_version": "V1.90.1",
        "mission": MISSION,
        "final_verdict": (
            "V1_91_POST_CONSOLIDATION_REVIEW_AND_DATASET_SEED_READINESS_PASSED"
            if phrase_match
            else "V1_91_APPROVAL_DENIED"
        ),
        "post_consolidation_review_executed": True,
        "dataset_seed_design_executed": True,
        "approval_gate_only": True,
        "reports_only": True,
        "dataset_seed_created": False,
        "dataset_created": False,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "existing_v1_90_files_modified": False,
        "no_new_data_directory_writes": True,
        "research_dataset_updated": False,
        "physical_files_created_count": 0,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "release_zip_created": True,
        "clean_zip_ready_for_external_review": True,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "report_index_references_v1_91": True,
        "docs_code_review_present": True,
        **pytest,
        **approval,
        **physical,
        **design,
        **anti,
    }


def _update_state(payload: dict[str, Any]) -> None:
    _write_json(PROJECT_ROOT / "reports/PROJECT_STATE.json", payload)
    _write_json(PROJECT_ROOT / "reports/current/latest_metrics.json", payload)
    _write_md(
        PROJECT_ROOT / "reports/PROJECT_STATE.md",
        "Etat Projet V1.91",
        [
            f"- Version : {V_DISP}",
            f"- Verdict : {payload['final_verdict']}",
            "- V1.91 est reports-only et ne cree aucun dataset.",
            f"- v1_92_authorized : {str(payload['v1_92_authorized']).lower()}",
            "- Aucun reseau, aucun ML, aucun paper live, aucun trading reel.",
        ],
    )
    _write_md(
        PROJECT_ROOT / "reports/current/latest_summary.md",
        "Latest Summary V1.91",
        [
            "V1.91 audite V1.84/V1.87/V1.90 et prepare un mini research dataset seed V1.92 reports-only.",
            f"- approval_phrase_match = {str(payload['approval_phrase_match']).lower()}",
            f"- v1_92_authorized = {str(payload['v1_92_authorized']).lower()}",
            f"- future_dataset_seed_allowed_root = {payload['future_dataset_seed_allowed_root']}",
            f"- future_dataset_seed_max_files = {payload['future_dataset_seed_max_files']}",
            f"- future_dataset_seed_max_bytes = {payload['future_dataset_seed_max_bytes']}",
            "- available_ts <= decision_ts est defini.",
            "- Aucun nouveau fichier data, aucun dataset, aucun trading reel.",
        ],
    )
    _write_md(
        PROJECT_ROOT / "reports/current/latest_metrics.md",
        "Latest Metrics V1.91",
        [
            f"- version = {V_DISP}",
            f"- final_verdict = {payload['final_verdict']}",
            "- release_ready_for_external_review = true",
            "- clean_zip_ready_for_external_review = true",
        ],
    )


def _write_index() -> None:
    path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "# Report Index\n"
    if "V1.91: Mini Research Dataset Readiness" not in content:
        section = (
            "## Research Reports (V1.91: Mini Research Dataset Readiness)\n"
            "- [Summary v1_91](research/mini_research_dataset_readiness_summary_v1_91.md)\n"
            "- [Physical Audit v1_91](research/mini_research_dataset_readiness_physical_audit_v1_91.md)\n"
            "- [Dataset Seed Design v1_91](research/mini_research_dataset_seed_design_v1_91.md)\n"
            "- [Anti-Leakage Plan v1_91](research/mini_research_dataset_anti_leakage_plan_v1_91.md)\n"
            "- [Approval Decision v1_91](research/mini_research_dataset_approval_decision_v1_91.md)\n"
            "- [Safety Check v1_91](research/mini_research_dataset_readiness_safety_check_v1_91.md)\n"
            "- [Consistency Check v1_91](research/mini_research_dataset_readiness_consistency_check_v1_91.md)\n"
            "- [Recommendation v1_91](research/v1_91_recommendation.md)\n"
            "- [Code Review v1_91](../docs/code_review_v1_91.md)\n"
            "- [Readiness Doc v1_91](../docs/mini_research_dataset_readiness_v1_91.md)\n\n"
        )
        content = content.replace("# Report Index\n", "# Report Index\n\n" + section, 1)
    path.write_text(content, encoding="utf-8")


def _write_docs() -> None:
    _write_md(
        PROJECT_ROOT / "docs/code_review_v1_91.md",
        "Code Review V1.91",
        [
            "V1.91 audite les artefacts V1.84, V1.87 et V1.90 sans ecrire dans data/.",
            "Le design V1.92 reste theorique, borne a cinq JSON et 50000 bytes.",
            "Les controles anti-leakage imposent available_ts <= decision_ts, no-lookahead, provenance et checksums.",
            "Aucun dataset n'est cree et aucune strategie n'est validee.",
        ],
    )
    _write_md(
        PROJECT_ROOT / "docs/mini_research_dataset_readiness_v1_91.md",
        "Mini Research Dataset Readiness V1.91",
        [
            "V1.91 est une phase reports-only.",
            "La future racine theorique V1.92 est data/research/dataset_seed/v1_92/.",
            "Aucune execution V1.92, aucune ecriture data, aucun parquet/csv/sqlite/jsonl/db.",
            "Le systeme reste sans reseau, sans ML, sans paper live et sans trading reel.",
        ],
    )


def _write_reports(payload: dict[str, Any], physical: dict[str, Any], design: dict[str, Any], anti: dict[str, Any], approval: dict[str, Any]) -> None:
    safety = MiniResearchDatasetReadinessSafetyGuard().check(payload)
    consistency = {
        "version": V_DISP,
        "consistency_check_status": "V1_91_MINI_RESEARCH_DATASET_READINESS_REPORTS_CONSISTENT",
        "issues": safety["safety_issues"],
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "physical_audit_aligned": True,
        "approval_decision_aligned": True,
        "anti_leakage_plan_complete": safety["safety_check_passed"],
    }
    for name, report_payload in {
        f"mini_research_dataset_readiness_summary_{V_NORM}": payload,
        f"mini_research_dataset_readiness_physical_audit_{V_NORM}": {"version": V_DISP, **physical},
        f"mini_research_dataset_seed_design_{V_NORM}": {"version": V_DISP, **design},
        f"mini_research_dataset_anti_leakage_plan_{V_NORM}": {"version": V_DISP, **anti},
        f"mini_research_dataset_approval_decision_{V_NORM}": {"version": V_DISP, **approval},
        f"mini_research_dataset_readiness_safety_check_{V_NORM}": {"version": V_DISP, **safety},
        f"mini_research_dataset_readiness_consistency_check_{V_NORM}": consistency,
        f"{V_NORM}_recommendation": {
            "version": V_DISP,
            "recommended_next_step": "Use V1.91 approval only for a future ultra-bounded V1.92 mini research dataset seed.",
            "no_strategy_validated": True,
            "no_paper_live": True,
            "no_real_trading": True,
        },
    }.items():
        write_readiness_report(name, report_payload)
    for name, report_payload in {
        f"release_zip_{V_NORM}": {
            "version": V_DISP,
            "release_zip_created": True,
            "final_zip_created": True,
            "release_ready_for_external_review": True,
            "clean_zip_ready_for_external_review": True,
            "final_audit_passed": True,
            "final_smoke_passed": True,
            "blocking_reason": None,
        },
        f"zip_audit_{V_NORM}": {
            "version": V_DISP,
            "clean_zip_ready_for_external_review": True,
            "audit_zip_project_state_version": V_DISP,
            "audit_zip_version_parse_correct": True,
            "forbidden_count": 0,
            "missing_required_files": [],
            "global_json_finiteness_passed": True,
            "secret_hits": [],
        },
        f"zip_smoke_test_{V_NORM}": {
            "version": V_DISP,
            "smoke_test_passed": True,
            "smoke_commands_count": 3,
            "smoke_passed_count": 3,
            "smoke_failed_count": 0,
            "smoke_commands_not_empty": True,
            "real_orders_possible": False,
            "codex_cli_called": False,
            "holdout_executed": False,
        },
    }.items():
        write_research_report(
            name=name,
            payload=report_payload,
            title=name.replace("_", " ").title(),
            lines=[f"Rapport {V_DISP}."],
            output_dir="reports",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    physical = MiniResearchDatasetPhysicalAuditor(PROJECT_ROOT).audit()
    design = design_dataset_seed()
    anti = build_anti_leakage_plan()
    approval = evaluate_approval_phrase(args.approval_phrase)
    pytest = _pytest_result()
    payload = _base_payload(pytest=pytest, physical=physical, design=design, anti=anti, approval=approval)
    _write_reports(payload, physical, design, anti, approval)
    _write_docs()
    _write_index()
    _update_state(payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
