from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from galapagos.research.refined_research_decision_gate_v9_4 import (
    build_manifest_v9_4,
    build_refined_research_decision_gate_v9_4,
)
from galapagos.research.refined_research_decision_gate_v9_4_validation import (
    validate_decision_payload_v9_4,
    validate_manifest_payload_v9_4,
    validate_markdown_text_v9_4,
)


ROOT = Path(__file__).resolve().parents[2]


def test_validator_v9_4_accepts_valid_decision_payload() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert validate_decision_payload_v9_4(payload) == []


def test_validator_v9_4_rejects_limited_backtest_candidate() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    payload["research_decision"] = "limited_research_backtest_candidate"

    errors = validate_decision_payload_v9_4(payload)

    assert any("must not authorize" in error for error in errors)


def test_validator_v9_4_rejects_claim_true() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    payload["findings"]["strategy_validated"] = True

    errors = validate_decision_payload_v9_4(payload)

    assert any("findings flags mismatch" in error for error in errors)


def test_validator_v9_4_rejects_safety_trading_true() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    payload["safety"]["trading_enabled"] = True

    errors = validate_decision_payload_v9_4(payload)

    assert any("safety flags mismatch" in error for error in errors)


def test_validator_v9_4_rejects_missing_label_shuffle_warning() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    payload["label_shuffle_assessment"]["no_clear_edge_vs_shuffled_labels_count"] = 0
    payload["label_shuffle_assessment"]["falsification_clean"] = True

    errors = validate_decision_payload_v9_4(payload)

    assert any("no-clear-edge" in error for error in errors)
    assert any("must not be marked clean" in error for error in errors)


def test_validator_v9_4_rejects_forbidden_metric_scan_failure() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    payload["metric_forbidden_scan"]["passed"] = False

    errors = validate_decision_payload_v9_4(payload)

    assert any("metric forbidden scan must pass" in error for error in errors)


def test_validator_v9_4_rejects_forbidden_markdown_claim() -> None:
    text = (
        "# Test\n\n"
        "Decision research.\n"
        "aucun backtest. aucun signal actionnable. aucun ordre. aucun trading reel.\n"
        "tradable edge confirmed.\n"
    )

    errors = validate_markdown_text_v9_4(text, "markdown fixture")

    assert any("tradable edge confirmed" in error for error in errors)


def test_validator_v9_4_accepts_valid_manifest_payload(tmp_path: Path) -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    report = tmp_path / "reports/research_decisions/refined_research_decision_gate_v9_4.json"
    report_md = tmp_path / "reports/research_decisions/refined_research_decision_gate_v9_4.md"
    doc = tmp_path / "docs/refined_research_decision_gate_v9_4.md"
    report.parent.mkdir(parents=True)
    doc.parent.mkdir(parents=True)
    report.write_text("{}", encoding="utf-8")
    report_md.write_text("# ok\n", encoding="utf-8")
    doc.write_text("# ok\n", encoding="utf-8")
    manifest = build_manifest_v9_4(tmp_path, payload)

    assert validate_manifest_payload_v9_4(manifest, payload) == []


def test_validator_v9_4_rejects_manifest_decision_mismatch(tmp_path: Path) -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)
    report = tmp_path / "reports/research_decisions/refined_research_decision_gate_v9_4.json"
    report_md = tmp_path / "reports/research_decisions/refined_research_decision_gate_v9_4.md"
    doc = tmp_path / "docs/refined_research_decision_gate_v9_4.md"
    report.parent.mkdir(parents=True)
    doc.parent.mkdir(parents=True)
    report.write_text("{}", encoding="utf-8")
    report_md.write_text("# ok\n", encoding="utf-8")
    doc.write_text("# ok\n", encoding="utf-8")
    manifest = build_manifest_v9_4(tmp_path, payload)
    manifest = deepcopy(manifest)
    manifest["research_decision"] = "stop_research_branch"

    errors = validate_manifest_payload_v9_4(manifest, payload)

    assert any("research_decision mismatch" in error for error in errors)
