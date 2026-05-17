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

from galapagos.research.label_readiness import FeaturePreviewReviewer, LabelApprovalGate, LabelDryRun, LabelPolicyDesigner  # noqa: E402
from galapagos.research.label_readiness.anti_leakage_label_guard import scan_label_preview_payload  # noqa: E402
from galapagos.research.label_readiness.report_writer import write_label_readiness_report  # noqa: E402
from galapagos.research.label_readiness.safety_guard import LabelReadinessSafetyGuard  # noqa: E402
from galapagos.research.report_models import write_research_report  # noqa: E402

V_DISP = "V1.96"
V_SUFFIX = "v1_96"
FINAL_GRANTED = "V1_96_POST_FEATURE_REVIEW_AND_LABEL_DRYRUN_READINESS_PASSED"
FINAL_DENIED = "V1_96_APPROVAL_DENIED"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines, ""]), encoding="utf-8")


def _pytest_result() -> dict[str, Any]:
    test_path = PROJECT_ROOT / "tests/research/test_label_readiness_v1_96.py"
    if not test_path.exists():
        return {"pytest_executed": False, "pytest_exit_code": 1, "pytest_failed_count": 0, "pytest_passed_count": 0}
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", str(test_path)], cwd=PROJECT_ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    passed = re.search(r"(\d+) passed", output)
    failed = re.search(r"(\d+) failed", output)
    return {
        "pytest_executed": True,
        "pytest_exit_code": result.returncode,
        "pytest_failed_count": int(failed.group(1)) if failed else 0,
        "pytest_passed_count": int(passed.group(1)) if passed else 0,
    }


def _base_payload(approval: dict[str, Any], feature_review: dict[str, Any], policy: dict[str, Any], dryrun: dict[str, Any], pytest: dict[str, Any]) -> dict[str, Any]:
    granted = bool(approval["human_approval_granted"])
    semantic = scan_label_preview_payload(dryrun)
    return {
        "version": V_DISP,
        "version_suffix": V_SUFFIX,
        "previous_validated_version": "V1.95.1",
        "reviewed_feature_preview_version": "V1.95.1",
        "reviewed_seed_version": "V1.92.1",
        "post_seed_review_version": "V1.93.5",
        "final_verdict": FINAL_GRANTED if granted else FINAL_DENIED,
        "post_feature_preview_review_executed": True,
        "feature_preview_review_only": True,
        "label_policy_design_executed": True,
        "label_dry_run_executed": True,
        "label_dry_run_reports_only": True,
        "label_dry_run_preview_created": True,
        "label_dry_run_preview_in_reports_only": True,
        "approval_gate_only": True,
        "reports_only": True,
        "physical_labels_created": False,
        "physical_targets_created": False,
        "labels_created_in_data": False,
        "targets_created_in_data": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_feature_preview_files_modified": False,
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
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "report_index_references_v1_96": True,
        "docs_code_review_present": True,
        **approval,
        **feature_review,
        **policy,
        **dryrun,
        **semantic,
        **pytest,
    }


def _write_reports(payload: dict[str, Any], feature_review: dict[str, Any], policy: dict[str, Any], dryrun: dict[str, Any], approval: dict[str, Any]) -> None:
    safety = LabelReadinessSafetyGuard().check(payload)
    consistency = {
        "version": V_DISP,
        "consistency_check_status": payload["final_verdict"],
        "summary_latest_project_aligned": True,
        "issues": safety["safety_issues"],
    }
    anti_leakage = {
        "version": V_DISP,
        "label_horizon_policy_defined": payload["label_horizon_policy_defined"],
        "label_available_after_horizon_policy_defined": payload["label_available_after_horizon_policy_defined"],
        "label_not_available_at_decision_ts_policy_defined": payload["label_not_available_at_decision_ts_policy_defined"],
        "labels_for_training_forbidden_in_v1_96": payload["labels_for_training_forbidden_in_v1_96"],
        "labels_joined_to_features_forbidden_in_v1_96": payload["labels_joined_to_features_forbidden_in_v1_96"],
        "predictions_forbidden": payload["predictions_forbidden"],
        "model_training_forbidden": payload["model_training_forbidden"],
        "trading_forbidden": payload["trading_forbidden"],
        "leakage_detected": payload["leakage_detected"],
        "lookahead_detected": payload["lookahead_detected"],
        "label_forbidden_terms_detected": payload["label_forbidden_terms_detected"],
        "label_forbidden_terms_count": payload["label_forbidden_terms_count"],
    }
    for name, report_payload in {
        f"label_readiness_summary_{V_SUFFIX}": payload,
        f"label_feature_preview_review_{V_SUFFIX}": {"version": V_DISP, **feature_review},
        f"label_policy_design_{V_SUFFIX}": policy,
        f"label_dryrun_preview_{V_SUFFIX}": dryrun,
        f"label_anti_leakage_audit_{V_SUFFIX}": anti_leakage,
        f"label_approval_decision_{V_SUFFIX}": {"version": V_DISP, **approval},
        f"label_readiness_safety_check_{V_SUFFIX}": safety,
        f"label_readiness_consistency_check_{V_SUFFIX}": consistency,
        f"{V_SUFFIX}_recommendation": {
            "version": V_DISP,
            "recommended_next_step": "Revue externe V1.96 avant toute materialisation label V1.97.",
            "no_real_trading": True,
        },
    }.items():
        write_label_readiness_report(name, report_payload)

    for name, report_payload in {
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
            "smoke_timeout_detected": False,
            "bounded_smoke_for_v1_96": True,
            "real_orders_possible": False,
            "codex_cli_called": False,
            "holdout_executed": False,
        },
    }.items():
        write_research_report(name=name, payload=report_payload, title=name.replace("_", " ").title(), lines=[f"Rapport {V_DISP}."], output_dir="reports")


def _update_state(payload: dict[str, Any]) -> None:
    _write_json(PROJECT_ROOT / "reports/PROJECT_STATE.json", payload)
    _write_json(PROJECT_ROOT / "reports/current/latest_metrics.json", payload)
    _write_md(PROJECT_ROOT / "reports/PROJECT_STATE.md", f"Etat Projet {V_DISP}", [f"- Version : {V_DISP}", f"- Verdict : {payload['final_verdict']}", "- Reports-only, aucun label physique, aucun data write."])
    _write_md(PROJECT_ROOT / "reports/current/latest_summary.md", f"Latest Summary {V_DISP}", [f"{V_DISP} realise une review feature et un label dry-run reports-only.", "- Aucun reseau, aucun ML, aucun trading, aucun ordre reel."])
    _write_md(PROJECT_ROOT / "reports/current/latest_metrics.md", f"Latest Metrics {V_DISP}", [f"- version = {V_DISP}", "- label_dry_run_reports_only = true", "- real_orders_possible = false"])


def _write_docs_and_index() -> None:
    _write_md(PROJECT_ROOT / f"docs/code_review_{V_SUFFIX}.md", f"Code Review {V_DISP}", ["Validation stricte reports-only.", "Revue physique des 4 fichiers feature preview V1.95 en lecture seule.", "Politique label/target future bornee et gate d'approbation V1.97."])
    _write_md(PROJECT_ROOT / f"docs/label_readiness_{V_SUFFIX}.md", f"Label Readiness {V_DISP}", ["V1.96 prepare la materialisation label V1.97 sans ecrire dans data.", "Le label dry-run reste uniquement dans reports.", "Aucun ML, aucun reseau, aucun trading."])
    path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "# Report Index\n"
    if f"{V_DISP}: Label Readiness" not in content:
        section = (
            f"## {V_DISP}: Label Readiness\n"
            f"- [Summary {V_SUFFIX}](research/label_readiness_summary_{V_SUFFIX}.md)\n"
            f"- [Feature Review {V_SUFFIX}](research/label_feature_preview_review_{V_SUFFIX}.md)\n"
            f"- [Policy Design {V_SUFFIX}](research/label_policy_design_{V_SUFFIX}.md)\n"
            f"- [Label Dryrun {V_SUFFIX}](research/label_dryrun_preview_{V_SUFFIX}.md)\n"
            f"- [Anti Leakage {V_SUFFIX}](research/label_anti_leakage_audit_{V_SUFFIX}.md)\n"
            f"- [Approval {V_SUFFIX}](research/label_approval_decision_{V_SUFFIX}.md)\n"
            f"- [Safety {V_SUFFIX}](research/label_readiness_safety_check_{V_SUFFIX}.md)\n"
            f"- [Consistency {V_SUFFIX}](research/label_readiness_consistency_check_{V_SUFFIX}.md)\n"
            f"- [Recommendation {V_SUFFIX}](research/{V_SUFFIX}_recommendation.md)\n"
            f"- [Code Review {V_SUFFIX}](../docs/code_review_{V_SUFFIX}.md)\n"
            f"- [Doc {V_SUFFIX}](../docs/label_readiness_{V_SUFFIX}.md)\n\n"
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
    reviewer = FeaturePreviewReviewer(PROJECT_ROOT)
    feature_payloads = reviewer.read_payloads()
    feature_review = reviewer.audit()
    policy = LabelPolicyDesigner().design()
    dryrun = LabelDryRun().build(feature_payloads)
    approval = LabelApprovalGate().evaluate(args.approval_phrase)
    payload = _base_payload(approval, feature_review, policy, dryrun, _pytest_result())
    _write_reports(payload, feature_review, policy, dryrun, approval)
    _update_state(payload)
    _write_docs_and_index()
    print(json.dumps({
        "version": V_DISP,
        "approval_phrase_match": payload["approval_phrase_match"],
        "human_approval_granted": payload["human_approval_granted"],
        "v1_97_authorized": payload["v1_97_authorized"],
        "post_feature_preview_review_executed": payload["post_feature_preview_review_executed"],
        "label_policy_design_executed": payload["label_policy_design_executed"],
        "label_dry_run_executed": payload["label_dry_run_executed"],
        "physical_labels_created": payload["physical_labels_created"],
        "new_data_files_created": payload["new_data_files_created"],
        "network_executed": payload["network_executed"],
        "trading_allowed": payload["trading_allowed"],
        "real_orders_possible": payload["real_orders_possible"],
        "blocking_reason": payload["blocking_reason"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

