from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from galapagos.research.alternative_label_design_audit_v9_5 import (
    build_alternative_label_design_audit_v9_5,
    build_manifest_v9_5,
)
from galapagos.research.alternative_label_design_audit_v9_5_validation import (
    validate_manifest_payload_v9_5,
    validate_markdown_text_v9_5,
    validate_report_payload_v9_5,
)


ROOT = Path(__file__).resolve().parents[2]


def test_validator_v9_5_accepts_valid_label_audit_payload() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    assert validate_report_payload_v9_5(payload) == []


def test_validator_v9_5_rejects_changed_v9_4_decision() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    payload["source_decision"]["research_decision"] = "limited_research_backtest_candidate"

    errors = validate_report_payload_v9_5(payload)

    assert any("conservative decision" in error for error in errors)


def test_validator_v9_5_rejects_missing_label_shuffle_evidence() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    payload["problem_diagnostic"]["no_clear_edge_vs_shuffled_labels_count"] = 0

    errors = validate_report_payload_v9_5(payload)

    assert any("label-shuffle no-clear-edge evidence" in error for error in errors)


def test_validator_v9_5_rejects_claim_true() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    payload["findings"]["strategy_validated"] = True

    errors = validate_report_payload_v9_5(payload)

    assert any("findings flags mismatch" in error for error in errors)


def test_validator_v9_5_rejects_safety_trading_true() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    payload["safety"]["trading_enabled"] = True

    errors = validate_report_payload_v9_5(payload)

    assert any("safety flag mismatch" in error for error in errors)


def test_validator_v9_5_rejects_leakage_guard_failure() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    payload["leakage_guard"]["passed"] = False

    errors = validate_report_payload_v9_5(payload)

    assert any("leakage guard must pass" in error for error in errors)


def test_validator_v9_5_rejects_forbidden_markdown_claim() -> None:
    text = (
        "# Audit\n\n"
        "aucun backtest. aucune strategie. aucun signal actionnable. aucun ordre. aucun trading reel.\n"
        "tradable edge confirmed.\n"
    )

    errors = validate_markdown_text_v9_5(text, "markdown fixture")

    assert any("tradable edge confirmed" in error for error in errors)


def test_validator_v9_5_accepts_valid_manifest_payload(tmp_path: Path) -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    report = tmp_path / "reports/research_decisions/alternative_label_design_audit_v9_5.json"
    report_md = tmp_path / "reports/research_decisions/alternative_label_design_audit_v9_5.md"
    doc = tmp_path / "docs/alternative_label_design_audit_v9_5.md"
    report.parent.mkdir(parents=True)
    doc.parent.mkdir(parents=True)
    report.write_text("{}", encoding="utf-8")
    report_md.write_text("# ok\n", encoding="utf-8")
    doc.write_text("# ok\n", encoding="utf-8")
    manifest = build_manifest_v9_5(tmp_path, payload)

    assert validate_manifest_payload_v9_5(manifest, payload) == []


def test_validator_v9_5_rejects_manifest_decision_mismatch(tmp_path: Path) -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)
    report = tmp_path / "reports/research_decisions/alternative_label_design_audit_v9_5.json"
    report_md = tmp_path / "reports/research_decisions/alternative_label_design_audit_v9_5.md"
    doc = tmp_path / "docs/alternative_label_design_audit_v9_5.md"
    report.parent.mkdir(parents=True)
    doc.parent.mkdir(parents=True)
    report.write_text("{}", encoding="utf-8")
    report_md.write_text("# ok\n", encoding="utf-8")
    doc.write_text("# ok\n", encoding="utf-8")
    manifest = build_manifest_v9_5(tmp_path, payload)
    manifest = deepcopy(manifest)
    manifest["v9_5_decision"]["decision"] = "stop_refined_branch_labels_not_promising"

    errors = validate_manifest_payload_v9_5(manifest, payload)

    assert any("manifest decision mismatch" in error for error in errors)
