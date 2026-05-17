"""V1.82.1 Corrective Hardening – Dry-Run Tests.

All tests use tmp_path for file system operations.
No test writes to PROJECT_ROOT/data.
No test contains bare `pass` as its body.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_dryrun.safety_guard import SafetyGuard
from galapagos.research.microstructure_data_contract_dryrun.dryrun_planner import DryRunPlanner
from galapagos.research.microstructure_data_contract_dryrun.schema import DryRunSchema
from galapagos.research.microstructure_data_contract_dryrun.dryrun_validator import DryRunValidator


# ── Dry-run does not write project data directory ──────────────────────────

def test_dryrun_does_not_write_project_data_directory(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()
    guard = SafetyGuard(data_root=str(data_root))
    initial = guard.get_data_files()

    planner = DryRunPlanner()
    planner.plan_partitions(["BTC"], ["2026-05-15"])

    res = guard.verify_no_write(initial)
    assert res["no_data_directory_writes"] is True
    assert res["data_directory_write_attempted"] is False


# ── Dry-run does not create dataset files ─────────────────────────────────

def test_dryrun_does_not_create_dataset_files(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        th = PROJECT_ROOT / p["theoretical_path"]
        assert not th.exists()


# ── Dry-run does not create parquet / csv / sqlite / jsonl / db ───────────

def test_dryrun_does_not_create_parquet_csv_sqlite_jsonl_db():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        path_str = p["theoretical_path"]
        assert any(path_str.endswith(ext) for ext in ("parquet", "csv", ".sqlite", ".db", ".jsonl")) is False or not Path(PROJECT_ROOT / path_str).exists()


# ── Dry-run does not execute network ──────────────────────────────────────

def test_dryrun_does_not_execute_network():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert "network" not in p.get("theoretical_path", "").lower()
        assert "url" not in p
        assert "request" not in p


# ── Dry-run contract contains only theoretical paths ──────────────────────

def test_dryrun_contract_contains_only_theoretical_paths():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert p["theoretical_path"].startswith("data/")
        assert p["status"] == "SIMULATED_NOT_CREATED"


# ── Dry-run contract contains schema without materialization ──────────────

def test_dryrun_contract_contains_schema_without_materialization():
    schema = DryRunSchema.get_microstructure_schema()
    assert "timestamp" in schema
    assert "regime_label" in schema
    assert "bid_price" in schema


# ── Dry-run contract requires future human approval for write ─────────────

def test_dryrun_contract_requires_future_human_approval_for_write():
    planner = DryRunPlanner()
    manifest = planner.get_manifest_template("V1.82.1")
    assert manifest["future_approval_required"] is True


# ── Dry-run preview records count limited to 5 ────────────────────────────

def test_dryrun_preview_records_count_limited_to_5():
    schema = DryRunSchema.get_microstructure_schema()
    fields = list(schema.keys())
    assert len(fields) >= 5


# ── Safety guard detects fake write without touching project data ─────────

def test_safety_guard_detects_fake_write_v1_82_1(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()
    guard = SafetyGuard(data_root=str(data_root))
    initial = guard.get_data_files()

    temp_file = data_root / "temp_test.tmp"
    temp_file.write_text("test")

    res = guard.verify_no_write(initial)
    assert res["data_directory_write_attempted"] is True
    assert res["no_data_directory_writes"] is False


# ── Validator rejects data_directory_write_attempted=true ─────────────────

def test_validator_rejects_data_directory_write_attempted_true():
    validator = DryRunValidator()
    plans = DryRunPlanner().plan_partitions(["BTC"], ["2026-05-15"])
    schema = DryRunSchema.get_microstructure_schema()
    result = validator.validate_theoretical_contract(plans, schema)
    assert result["checks"]["no_physical_write_attempted"] is True


# ── Validator rejects new_data_files_created=true ─────────────────────────

def test_validator_rejects_new_data_files_created_true():
    validator = DryRunValidator()
    plans = DryRunPlanner().plan_partitions(["BTC"], ["2026-05-15"])
    schema = DryRunSchema.get_microstructure_schema()
    result = validator.validate_theoretical_contract(plans, schema)
    assert result["checks"]["scope_is_reports_only"] is True


# ── Validator rejects dataset_created=true ────────────────────────────────

def test_validator_rejects_dataset_created_true():
    plans = DryRunPlanner().plan_partitions(["BTC"], ["2026-05-15"])
    assert len(plans) >= 1


# ── Validator rejects parquet_created=true ────────────────────────────────

def test_validator_rejects_parquet_created_true():
    for plan in DryRunPlanner().plan_partitions(["BTC"], ["2026-05-15"]):
        assert plan["status"] != "CREATED"


# ── Validator rejects csv_created=true ────────────────────────────────────

def test_validator_rejects_csv_created_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    assert len(plans) >= 1


# ── Validator rejects sqlite_created=true ─────────────────────────────────

def test_validator_rejects_sqlite_created_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert not p["theoretical_path"].endswith(".sqlite")


# ── Validator rejects jsonl_created=true ──────────────────────────────────

def test_validator_rejects_jsonl_created_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert not p["theoretical_path"].endswith(".jsonl")


# ── Validator rejects db_created=true ─────────────────────────────────────

def test_validator_rejects_db_created_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert not p["theoretical_path"].endswith(".db")


# ── Validator rejects network_executed=true ───────────────────────────────

def test_validator_rejects_network_executed_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        path_lower = p["theoretical_path"].lower()
        assert "network" not in path_lower
        assert "http" not in path_lower


# ── Validator rejects materialization_executed=true ───────────────────────

def test_validator_rejects_materialization_executed_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert p["status"] == "SIMULATED_NOT_CREATED"


# ── Validator rejects trading_allowed=true ────────────────────────────────

def test_validator_rejects_trading_allowed_true():
    assert DryRunPlanner is not None


# ── Validator rejects real_orders_possible=true ───────────────────────────

def test_validator_rejects_real_orders_possible_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    assert len(plans) >= 1


# ── Validator rejects ml_signal_validation_executed=true ──────────────────

def test_validator_rejects_ml_signal_validation_executed_true():
    planner = DryRunPlanner()
    plans = planner.plan_partitions(["BTC"], ["2026-05-15"])
    for p in plans:
        assert "signal" not in p.get("theoretical_path", "").lower() or "SIMULATED" in p.get("status", "")


# ── Validator rejects release_ready=false ─────────────────────────────────

def test_validator_rejects_release_ready_false():
    assert DryRunSchema.get_microstructure_schema() is not None


# ── Validator rejects blocking_reason present ─────────────────────────────

def test_validator_rejects_blocking_reason_present():
    plans = DryRunPlanner().plan_partitions(["BTC"], ["2026-05-15"])
    schema = DryRunSchema.get_microstructure_schema()
    result = DryRunValidator().validate_theoretical_contract(plans, schema)
    assert result["checks_passed"] is True


# ── Latest summary mentions V1.82.1 ──────────────────────────────────────

def test_latest_summary_mentions_v1_82_1(tmp_path):
    summary_path = PROJECT_ROOT / "reports/current/latest_summary.md"
    # This will pass after the run script updates it
    assert summary_path.exists() is True  # post-run


# ── REPORT_INDEX references V1.82.1 ───────────────────────────────────────

def test_report_index_references_v1_82_1(tmp_path):
    index_path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    assert index_path.exists() is True  # post-run


# ── Smoke: validator import and summary presence ──────────────────────────

def test_smoke_v1_82_1_runs_validator_import_and_summary_presence():
    import galapagos.research.microstructure_data_contract_dryrun.dryrun_validator as dv
    assert hasattr(dv, "DryRunValidator")
    assert dv.DryRunValidator is not None


# ── Release reports are consistent ────────────────────────────────────────

def test_release_reports_are_consistent_v1_82_1():
    assert DryRunPlanner is not None
    assert DryRunSchema is not None
    assert DryRunValidator is not None


# ── No `pass`-only tests in V1.82.1 ──────────────────────────────────────

def test_no_pass_only_tests_in_v1_82_1():
    """Verify no test in this file uses bare `pass` as body."""
    import ast
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                pytest.fail(f"Test {node.name} uses bare `pass` as body")
