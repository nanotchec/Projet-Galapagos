from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from galapagos.research.feature_preview_materialization.feature_preview_builder import EXPECTED_FILES
from galapagos.research.feature_preview_materialization.feature_semantic_guard import scan_feature_payloads
from galapagos.research.feature_preview_materialization.validator import validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSION = "V1.95.1"
VERSION_SUFFIX = "v1_95_1"
ROOT = Path("data/research/feature_preview/v1_95")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_preview(root: Path) -> dict:
    out = root / ROOT
    out.mkdir(parents=True, exist_ok=True)
    schema = {"version": VERSION, "features": [{"feature_name": "spread_bps"}, {"feature_name": "mid_price"}]}
    rows = {
        "version": VERSION,
        "rows": [
            {
                "event_ts": "2026-01-01T00:00:00Z",
                "available_ts": "2026-01-01T00:00:01Z",
                "decision_ts": "2026-01-01T00:00:01Z",
                "spread_bps": None,
            }
        ],
    }
    quality = {"version": VERSION, "preview_rows_count": 1, "theoretical_features_count": 2}
    _write_json(out / "feature_preview_schema.json", schema)
    _write_json(out / "feature_preview_rows.json", rows)
    _write_json(out / "feature_preview_quality_audit.json", quality)
    checksums = {name: _sha256(out / name) for name in EXPECTED_FILES if name != "feature_preview_manifest.json"}
    manifest = {
        "version": VERSION,
        "feature_preview_file_checksums": checksums,
        "created_files": [str(ROOT / name) for name in EXPECTED_FILES],
    }
    _write_json(out / "feature_preview_manifest.json", manifest)
    return {"schema": schema, "rows": rows, "quality": quality, "manifest": manifest}


def _write_seed(root: Path) -> None:
    seed_root = root / "data/research/dataset_seed/v1_92"
    seed_root.mkdir(parents=True, exist_ok=True)
    payloads = {
        "seed_schema.json": {"fields": [{"name": "available_ts"}, {"name": "decision_ts"}]},
        "seed_preview_records.json": {
            "records": [{"available_ts": "2026-01-01T00:00:01Z", "decision_ts": "2026-01-01T00:00:01Z"}]
        },
        "seed_provenance.json": {"sources": ["V1.92.1"]},
        "seed_quality_audit.json": {"ok": True},
    }
    for name, payload in payloads.items():
        _write_json(seed_root / name, payload)
    _write_json(
        seed_root / "seed_manifest.json",
        {"seed_file_checksums": {name: _sha256(seed_root / name) for name in payloads}},
    )


@pytest.fixture
def mock_reports(tmp_path: Path) -> Path:
    _write_seed(tmp_path)
    physical_payloads = _write_preview(tmp_path)
    semantic = scan_feature_payloads(physical_payloads)
    summary = {
        "version": VERSION,
        "final_verdict": "V1_95_1_FEATURE_PREVIEW_MATERIALIZATION_TIMESTAMP_AUDIT_PASSED",
        "feature_preview_materialization_executed": True,
        "feature_preview_only": True,
        "physical_features_created": True,
        "feature_files_created_in_data": True,
        "full_feature_dataset_created": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "total_new_data_files_created": 4,
        "created_files_count": 4,
        "total_data_bytes_written": sum((tmp_path / ROOT / name).stat().st_size for name in EXPECTED_FILES),
        "preview_rows_count": 1,
        "theoretical_features_count": 2,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "existing_seed_files_modified": False,
        "physical_timestamp_order_scan_executed": True,
        "feature_rows_timestamp_order_valid": True,
        "available_ts_lte_decision_ts_checked": True,
        "event_ts_lte_available_ts_checked": True,
        "timestamp_order_violations_detected": False,
        "timestamp_order_violations_count": 0,
        "timestamp_order_violations": [],
        **semantic,
    }
    for folder in ["reports/research", "reports/current", "docs"]:
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    for relative, payload in {
        f"reports/research/feature_preview_materialization_summary_{VERSION_SUFFIX}.json": summary,
        f"reports/research/feature_preview_materialization_file_audit_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            **summary,
            "feature_preview_json_valid": True,
            "feature_preview_checksums_verified": True,
            "missing_expected_files_count": 0,
            "unexpected_files_count": 0,
        },
        f"reports/research/feature_preview_materialization_semantic_audit_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            **semantic,
        },
        f"reports/research/feature_preview_materialization_timestamp_audit_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "physical_timestamp_order_scan_executed": True,
            "feature_rows_timestamp_order_valid": True,
            "available_ts_lte_decision_ts_checked": True,
            "event_ts_lte_available_ts_checked": True,
            "timestamp_order_violations_detected": False,
            "timestamp_order_violations_count": 0,
            "timestamp_order_violations": [],
        },
        f"reports/research/feature_preview_materialization_safety_check_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "safety_check_passed": True,
        },
        f"reports/research/feature_preview_materialization_consistency_check_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "issues": [],
        },
        "reports/current/latest_metrics.json": summary,
        "reports/PROJECT_STATE.json": summary,
        f"reports/release_zip_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "release_zip_created": True,
            "final_zip_created": True,
            "release_ready_for_external_review": True,
            "clean_zip_ready_for_external_review": True,
            "final_audit_passed": True,
            "final_smoke_passed": True,
            "blocking_reason": None,
        },
        f"reports/zip_audit_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "clean_zip_ready_for_external_review": True,
            "audit_zip_project_state_version": VERSION,
            "audit_zip_version_parse_correct": True,
            "global_json_finiteness_passed": True,
            "missing_required_files": [],
            "forbidden_count": 0,
        },
        f"reports/zip_smoke_test_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "smoke_test_passed": True,
            "smoke_failed_count": 0,
            "smoke_passed_count": 3,
            "smoke_commands_count": 3,
            "smoke_commands_not_empty": True,
            "bounded_smoke_for_v1_95_1": True,
            "real_orders_possible": False,
            "codex_cli_called": False,
            "holdout_executed": False,
        },
    }.items():
        _write_json(tmp_path / relative, payload)
        (tmp_path / relative).with_suffix(".md").write_text("# Rapport", encoding="utf-8")
    (tmp_path / "reports/REPORT_INDEX.md").write_text(f"V1.95.1 {VERSION_SUFFIX}", encoding="utf-8")
    (tmp_path / f"docs/code_review_{VERSION_SUFFIX}.md").write_text("Review", encoding="utf-8")
    (tmp_path / f"docs/feature_preview_materialization_{VERSION_SUFFIX}.md").write_text("Doc", encoding="utf-8")
    return tmp_path


def _mutate_json(root: Path, relative: str, **updates: object) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    _write_json(path, payload)


def _set_state(root: Path, field: str, value: object) -> None:
    for relative in [
        f"reports/research/feature_preview_materialization_summary_{VERSION_SUFFIX}.json",
        "reports/current/latest_metrics.json",
        "reports/PROJECT_STATE.json",
    ]:
        _mutate_json(root, relative, **{field: value})


def _errors(root: Path) -> list[str]:
    return validate_report_set(root, VERSION_SUFFIX)


def test_validator_succeeds_on_mock_reports(mock_reports: Path) -> None:
    assert _errors(mock_reports) == []


def test_requires_v1_94_approval() -> None:
    approval = json.loads(
        (PROJECT_ROOT / "reports/research/causal_feature_approval_decision_v1_94.json").read_text(encoding="utf-8")
    )
    assert approval["v1_95_authorized"] is True


def test_feature_preview_writes_exactly_four_json_files(mock_reports: Path) -> None:
    files = sorted(p.name for p in (mock_reports / ROOT).glob("*"))
    assert files == sorted(EXPECTED_FILES)


@pytest.mark.parametrize("field", ["created_files_count", "total_new_data_files_created"])
def test_rejects_more_than_four_files(mock_reports: Path, field: str) -> None:
    _set_state(mock_reports, field, 5)
    errors = _errors(mock_reports)
    assert any("diverges from physical audit" in e or f"{field} != " in e for e in errors)


def test_rejects_unapproved_write_path(mock_reports: Path) -> None:
    (mock_reports / ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert "feature preview files are not exact" in _errors(mock_reports)


def test_rejects_bytes_over_limit(mock_reports: Path) -> None:
    _set_state(mock_reports, "total_data_bytes_written", 50001)
    errors = _errors(mock_reports)
    assert any("total_data_bytes_written > 50000" in e or "diverges from physical audit" in e for e in errors)


def test_rejects_preview_rows_above_10(mock_reports: Path) -> None:
    _set_state(mock_reports, "preview_rows_count", 11)
    errors = _errors(mock_reports)
    assert any("preview_rows_count > 10" in e or "diverges from physical audit" in e for e in errors)


def test_rejects_theoretical_features_above_20(mock_reports: Path) -> None:
    _set_state(mock_reports, "theoretical_features_count", 21)
    errors = _errors(mock_reports)
    assert any("theoretical_features_count > 20" in e or "diverges from physical audit" in e for e in errors)


@pytest.mark.parametrize(
    "field",
    [
        "labels_created",
        "targets_created",
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
    ],
)
def test_rejects_safety_flags(mock_reports: Path, field: str) -> None:
    _set_state(mock_reports, field, True)
    errors = _errors(mock_reports)
    assert any(f"{field} != " in e for e in errors)


def test_rejects_existing_seed_files_modified(mock_reports: Path) -> None:
    _set_state(mock_reports, "existing_seed_files_modified", True)
    errors = _errors(mock_reports)
    assert any("existing_seed_files_modified != " in e for e in errors)


@pytest.mark.parametrize(
    "term",
    [
        "target_return",
        "future_return_1h",
        "prediction_score",
        "label_up_down",
        "pnl",
        "profit",
        "expected_value",
        "mfe",
        "mae",
    ],
)
def test_rejects_forbidden_terms_anywhere(term: str) -> None:
    scan = scan_feature_payloads({"feature_preview_schema.json": {"features": [{"feature_name": term}]}})
    assert scan["forbidden_feature_terms_detected"] is True


def test_rejects_target_return_in_feature_schema_even_with_recomputed_manifest(mock_reports: Path) -> None:
    path = mock_reports / ROOT / "feature_preview_schema.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["features"].append({"feature_name": "target_return"})
    _write_json(path, payload)
    manifest = json.loads((mock_reports / ROOT / "feature_preview_manifest.json").read_text(encoding="utf-8"))
    manifest["feature_preview_file_checksums"]["feature_preview_schema.json"] = _sha256(path)
    _write_json(mock_reports / ROOT / "feature_preview_manifest.json", manifest)
    assert any("forbidden feature terms detected" in e or "diverges from physical audit" in e for e in _errors(mock_reports))


def test_rejects_future_return_in_feature_rows_even_with_recomputed_manifest(mock_reports: Path) -> None:
    path = mock_reports / ROOT / "feature_preview_rows.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][0]["future_return_1h"] = 0.1
    _write_json(path, payload)
    manifest = json.loads((mock_reports / ROOT / "feature_preview_manifest.json").read_text(encoding="utf-8"))
    manifest["feature_preview_file_checksums"]["feature_preview_rows.json"] = _sha256(path)
    _write_json(mock_reports / ROOT / "feature_preview_manifest.json", manifest)
    assert any("forbidden feature terms detected" in e or "diverges from physical audit" in e for e in _errors(mock_reports))


def test_feature_rows_have_available_ts_and_decision_ts(mock_reports: Path) -> None:
    rows = json.loads((mock_reports / ROOT / "feature_preview_rows.json").read_text(encoding="utf-8"))["rows"]
    row_keys = set(rows[0].keys())
    assert "available_ts" in row_keys
    assert "decision_ts" in row_keys


def test_feature_rows_respect_available_ts_lte_decision_ts(mock_reports: Path) -> None:
    row = json.loads((mock_reports / ROOT / "feature_preview_rows.json").read_text(encoding="utf-8"))["rows"][0]
    assert row["available_ts"] <= row["decision_ts"]


def test_manifest_contains_checksums(mock_reports: Path) -> None:
    manifest = json.loads((mock_reports / ROOT / "feature_preview_manifest.json").read_text(encoding="utf-8"))
    assert "feature_preview_file_checksums" in manifest


def test_validator_rejects_forbidden_feature_terms_detected_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "forbidden_feature_terms_detected", True)
    errors = _errors(mock_reports)
    assert any("forbidden_feature_terms_detected != " in e for e in errors)


def test_validator_rejects_forbidden_feature_terms_count_positive(mock_reports: Path) -> None:
    _set_state(mock_reports, "forbidden_feature_terms_count", 1)
    errors = _errors(mock_reports)
    assert any("forbidden_feature_terms_count != " in e for e in errors)


def test_validator_rejects_non_empty_forbidden_feature_term_occurrences(mock_reports: Path) -> None:
    _set_state(
        mock_reports, "forbidden_feature_term_occurrences", [{"file": "x", "json_path": "y", "matched_term": "target"}]
    )
    errors = _errors(mock_reports)
    assert any("forbidden_feature_term_occurrences != " in e for e in errors)


def test_report_index_references_v1_95_1(mock_reports: Path) -> None:
    content = (mock_reports / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    assert "V1.95.1" in content
    assert "v1_95_1" in content


def test_smoke_v1_95_1_runs_validator_import_and_summary_presence() -> None:
    content = (PROJECT_ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_feature_preview_materialization_v1_95_1_reports.py" in content


def test_cross_file_alignment_summary_latest_metrics_project_state(mock_reports: Path) -> None:
    assert not _errors(mock_reports)
    _mutate_json(mock_reports, "reports/current/latest_metrics.json", version="V1.94")
    assert len(_errors(mock_reports)) > 0


def test_no_pass_only_tests_in_v1_95_1() -> None:
    path = PROJECT_ROOT / "tests/research/test_feature_preview_materialization_v1_95_1.py"
    if path.exists():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders = [
            n.name
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and n.name.startswith("test_")
            and len(n.body) == 1
            and isinstance(n.body[0], ast.Pass)
        ]
        assert offenders == []


def test_no_assert_true_or_true_in_v1_95_1() -> None:
    path = PROJECT_ROOT / "tests/research/test_feature_preview_materialization_v1_95_1.py"
    if path.exists():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert [
            n.lineno
            for n in ast.walk(tree)
            if isinstance(n, ast.Assert) and isinstance(n.test, ast.Constant) and n.test.value is True
        ] == []
        assert [
            n.lineno
            for n in ast.walk(tree)
            if isinstance(n, ast.BoolOp)
            and isinstance(n.op, ast.Or)
            and any(isinstance(v, ast.Constant) and v.value is True for v in n.values)
        ] == []
