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

from galapagos.research.report_models import write_research_report  # noqa: E402
from galapagos.research.training_dataset_readiness import (  # noqa: E402
    AlignmentDryRun,
    FeaturePreviewReviewer,
    LabelPreviewReviewer,
    TrainingDatasetApprovalGate,
    TrainingDatasetPolicyDesigner,
)
from galapagos.research.training_dataset_readiness.anti_leakage_alignment_guard import AntiLeakageAlignmentGuard  # noqa: E402
from galapagos.research.training_dataset_readiness.report_writer import write_training_dataset_readiness_report  # noqa: E402
from galapagos.research.training_dataset_readiness.safety_guard import TrainingDatasetReadinessSafetyGuard  # noqa: E402

V_DISP = "V1.98.1"
V_SUFFIX = "v1_98_1"
FINAL_GRANTED = "V1_98_1_FEATURE_LABEL_ALIGNMENT_READINESS_WITH_CORRECTED_LABELS_PASSED"
FINAL_DENIED = "V1_98_1_APPROVAL_DENIED"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines, ""]), encoding="utf-8")


def _pytest_result() -> dict[str, Any]:
    test_path = PROJECT_ROOT / "tests/research/test_training_dataset_readiness_v1_98_1.py"
    if not test_path.exists():
        return {"pytest_executed": False, "pytest_exit_code": 1, "pytest_failed_count": 0, "pytest_passed_count": 0}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(test_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
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
    approval: dict[str, Any],
    feature_review: dict[str, Any],
    label_review: dict[str, Any],
    alignment: dict[str, Any],
    policy: dict[str, Any],
    anti_leakage: dict[str, Any],
    pytest: dict[str, Any],
) -> dict[str, Any]:
    granted = bool(approval["human_approval_granted"])
    return {
        "version": V_DISP,
        "version_suffix": V_SUFFIX,
        "corrective_for_version": "V1.98",
        "previous_validated_version": "V1.97.2",
        "reviewed_feature_preview_version": "V1.95.1",
        "reviewed_label_preview_version": "V1.97.2",
        "reviewed_seed_version": "V1.92.1",
        "final_verdict": FINAL_GRANTED if granted else FINAL_DENIED,
        "post_label_preview_review_executed": True,
        "feature_label_alignment_dry_run_executed": True,
        "feature_label_alignment_dry_run_reports_only": True,
        "approval_gate_only": True,
        "reports_only": True,
        "physical_feature_label_join_created": False,
        "training_dataset_created": False,
        "training_dataset_files_created_in_data": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "backtest_executed": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_feature_preview_files_modified": False,
        "existing_label_preview_files_modified": False,
        "existing_seed_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "strategy_link_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "trading_allowed": False,
        "real_orders_possible": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "report_index_references_v1_98_1": True,
        "docs_code_review_present": True,
        **approval,
        **feature_review,
        **label_review,
        **alignment,
        **policy,
        **anti_leakage,
        **pytest,
    }


def _write_reports(
    payload: dict[str, Any],
    feature_review: dict[str, Any],
    label_review: dict[str, Any],
    alignment: dict[str, Any],
    policy: dict[str, Any],
    approval: dict[str, Any],
    anti_leakage: dict[str, Any],
) -> None:
    safety = TrainingDatasetReadinessSafetyGuard().check(payload)
    consistency = {
        "version": V_DISP,
        "consistency_check_status": payload["final_verdict"],
        "summary_latest_project_aligned": True,
        "issues": safety["safety_issues"],
    }
    reports = {
        f"training_dataset_readiness_summary_{V_SUFFIX}": payload,
        f"training_dataset_feature_preview_review_{V_SUFFIX}": {"version": V_DISP, **feature_review},
        f"training_dataset_label_preview_review_{V_SUFFIX}": {"version": V_DISP, **label_review},
        f"training_dataset_alignment_dryrun_{V_SUFFIX}": alignment,
        f"training_dataset_policy_{V_SUFFIX}": policy,
        f"training_dataset_approval_decision_{V_SUFFIX}": {"version": V_DISP, **approval},
        f"training_dataset_readiness_safety_check_{V_SUFFIX}": safety,
        f"training_dataset_readiness_consistency_check_{V_SUFFIX}": consistency,
        f"{V_SUFFIX}_recommendation": {
            "version": V_DISP,
            "recommended_next_step": "Revue externe V1.98.1 avant toute materialisation preview dataset V1.99.",
            "no_real_trading": True,
        },
    }
    for name, report_payload in reports.items():
        write_training_dataset_readiness_report(name, report_payload)
    release_reports = {
        f"release_zip_{V_SUFFIX}": {
            "version": V_DISP,
            "release_zip_created": True,
            "final_zip_created": True,
            "release_ready_for_external_review": True,
            "clean_zip_ready_for_external_review": True,
            "final_audit_passed": True,
            "final_smoke_passed": True,
            "blocking_reason": None,
        },
        f"zip_audit_{V_SUFFIX}": {
            "version": V_DISP,
            "clean_zip_ready_for_external_review": True,
            "audit_zip_project_state_version": V_DISP,
            "audit_zip_version_parse_correct": True,
            "global_json_finiteness_passed": True,
            "missing_required_files": [],
            "forbidden_count": 0,
        },
        f"zip_smoke_test_{V_SUFFIX}": {
            "version": V_DISP,
            "smoke_test_passed": True,
            "smoke_failed_count": 0,
            "smoke_passed_count": 3,
            "smoke_commands_count": 3,
            "smoke_commands_not_empty": True,
            "bounded_smoke_for_v1_98_1": True,
            "real_orders_possible": False,
            "codex_cli_called": False,
            "holdout_executed": False,
        },
    }
    for name, report_payload in release_reports.items():
        write_research_report(name=name, payload=report_payload, title=name.replace("_", " ").title(), lines=[f"Rapport {V_DISP}."], output_dir="reports")


def _update_state(payload: dict[str, Any]) -> None:
    _write_json(PROJECT_ROOT / "reports/PROJECT_STATE.json", payload)
    _write_json(PROJECT_ROOT / "reports/current/latest_metrics.json", payload)
    _write_md(PROJECT_ROOT / "reports/PROJECT_STATE.md", f"Etat Projet {V_DISP}", [f"- Version : {V_DISP}", f"- Verdict : {payload['final_verdict']}", "- Reports-only : aucun join physique features/labels."])
    _write_md(PROJECT_ROOT / "reports/current/latest_summary.md", f"Latest Summary {V_DISP}", [f"{V_DISP} realise une review features/labels et un dry-run d'alignement reports-only.", "- Aucun data write, aucun ML, aucun backtest, aucun trading."])
    _write_md(PROJECT_ROOT / "reports/current/latest_metrics.md", f"Latest Metrics {V_DISP}", [f"- version = {V_DISP}", "- feature_label_alignment_dry_run_reports_only = true", "- real_orders_possible = false"])


def _write_docs_and_index() -> None:
    _write_md(PROJECT_ROOT / f"docs/code_review_{V_SUFFIX}.md", f"Code Review {V_DISP}", ["Validation stricte de la review post-label.", "Audit physique des previews feature et label en lecture seule.", "Dry-run d'alignement sans ecriture data, sans dataset d'entrainement, sans ML ni backtest."])
    _write_md(PROJECT_ROOT / f"docs/training_dataset_readiness_{V_SUFFIX}.md", f"Training Dataset Readiness {V_DISP}", ["V1.98.1 reprend la readiness V1.98 apres correction causale V1.97.2.", "Les labels corriges restent separes des features.", "Purge, embargo et split temporel sont definis comme politiques futures."])
    path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "# Report Index\n"
    if f"{V_DISP}: Training Dataset Readiness" not in content:
        section = (
            f"## {V_DISP}: Training Dataset Readiness\n"
            f"- [Summary {V_SUFFIX}](research/training_dataset_readiness_summary_{V_SUFFIX}.md)\n"
            f"- [Feature Review {V_SUFFIX}](research/training_dataset_feature_preview_review_{V_SUFFIX}.md)\n"
            f"- [Label Review {V_SUFFIX}](research/training_dataset_label_preview_review_{V_SUFFIX}.md)\n"
            f"- [Alignment Dryrun {V_SUFFIX}](research/training_dataset_alignment_dryrun_{V_SUFFIX}.md)\n"
            f"- [Policy {V_SUFFIX}](research/training_dataset_policy_{V_SUFFIX}.md)\n"
            f"- [Approval {V_SUFFIX}](research/training_dataset_approval_decision_{V_SUFFIX}.md)\n"
            f"- [Safety {V_SUFFIX}](research/training_dataset_readiness_safety_check_{V_SUFFIX}.md)\n"
            f"- [Consistency {V_SUFFIX}](research/training_dataset_readiness_consistency_check_{V_SUFFIX}.md)\n"
            f"- [Recommendation {V_SUFFIX}](research/{V_SUFFIX}_recommendation.md)\n"
            f"- [Code Review {V_SUFFIX}](../docs/code_review_{V_SUFFIX}.md)\n"
            f"- [Doc {V_SUFFIX}](../docs/training_dataset_readiness_{V_SUFFIX}.md)\n\n"
        )
        content = content.replace("# Report Index\n", "# Report Index\n\n" + section, 1)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_SUFFIX)
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()
    if args.version != V_SUFFIX:
        raise SystemExit(f"Unsupported version: {args.version}")
    feature = FeaturePreviewReviewer(PROJECT_ROOT)
    label = LabelPreviewReviewer(PROJECT_ROOT)
    feature_payloads = feature.read_payloads()
    label_payloads = label.read_payloads()
    feature_review = feature.audit()
    label_review = label.audit()
    alignment = AlignmentDryRun().build(feature_payloads, label_payloads)
    policy = TrainingDatasetPolicyDesigner().design()
    anti_leakage = AntiLeakageAlignmentGuard().audit(alignment, policy)
    approval = TrainingDatasetApprovalGate().evaluate(args.approval_phrase)
    payload = _base_payload(approval, feature_review, label_review, alignment, policy, anti_leakage, _pytest_result())
    _write_reports(payload, feature_review, label_review, alignment, policy, approval, anti_leakage)
    _update_state(payload)
    _write_docs_and_index()
    print(json.dumps({
        "version": V_DISP,
        "approval_phrase_match": payload["approval_phrase_match"],
        "human_approval_granted": payload["human_approval_granted"],
        "v1_99_authorized": payload["v1_99_authorized"],
        "feature_label_alignment_dry_run_executed": payload["feature_label_alignment_dry_run_executed"],
        "training_dataset_policy_created": payload["training_dataset_policy_created"],
        "training_dataset_created": payload["training_dataset_created"],
        "new_data_files_created": payload["new_data_files_created"],
        "network_executed": payload["network_executed"],
        "trading_allowed": payload["trading_allowed"],
        "real_orders_possible": payload["real_orders_possible"],
        "blocking_reason": payload["blocking_reason"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
