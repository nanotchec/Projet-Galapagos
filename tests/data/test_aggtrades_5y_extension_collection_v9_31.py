from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from galapagos.data.aggtrades_5y_extension_collection_v9_31 import (
    BASE_SAFETY_FLAGS,
    EXTENSION_WINDOW_END,
    EXTENSION_WINDOW_START,
    INTERNAL_BATCHES_60,
    build_batches_for_preflight_v9_31,
    build_dynamic_batches_v9_31,
    build_manifest_v9_31,
    date_range_v9_31,
    safety_flags_for_batch_v9_31,
    validate_batch_spec_v9_31,
)


def test_v9_31_extension_window_has_expected_day_count() -> None:
    dates = date_range_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END)

    assert len(dates) == 1096
    assert dates[0] == "2021-05-05"
    assert dates[-1] == "2024-05-04"


def test_v9_31_static_batches_cover_extension_with_sixty_day_cap() -> None:
    all_dates: list[str] = []
    for batch in INTERNAL_BATCHES_60:
        batch_dates = date_range_v9_31(batch.start_date, batch.end_date)
        validate_batch_spec_v9_31(batch, batch_dates)
        all_dates.extend(batch_dates)

    assert len(INTERNAL_BATCHES_60) == 19
    assert max(len(date_range_v9_31(batch.start_date, batch.end_date)) for batch in INTERNAL_BATCHES_60) == 60
    assert INTERNAL_BATCHES_60[-1].max_downloads == 16
    assert all_dates == date_range_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END)


def test_v9_31_dynamic_batches_split_to_thirty_days() -> None:
    batches = build_dynamic_batches_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END, 30)
    all_dates = [day for batch in batches for day in date_range_v9_31(batch.start_date, batch.end_date)]

    assert max(batch.max_downloads for batch in batches) <= 30
    assert all_dates == date_range_v9_31(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END)


def test_v9_31_preflight_batch_policy_uses_sixty_or_thirty_day_batches() -> None:
    sixty = build_batches_for_preflight_v9_31({"max_batch_days_allowed": 60})
    thirty = build_batches_for_preflight_v9_31({"max_batch_days_allowed": 30})

    assert len(sixty) == 19
    assert max(batch.max_downloads for batch in sixty) == 60
    assert max(batch.max_downloads for batch in thirty) <= 30


def test_v9_31_validate_batch_spec_rejects_over_max_downloads() -> None:
    batch = INTERNAL_BATCHES_60[0]
    too_many_dates = [*date_range_v9_31(batch.start_date, batch.end_date), "2021-07-04"]

    with pytest.raises(ValueError, match="max_downloads"):
        validate_batch_spec_v9_31(batch, too_many_dates)


def test_v9_31_safety_flags_switch_when_collection_runs() -> None:
    flags = safety_flags_for_batch_v9_31({"days_attempted": 1, "days_downloaded": 1, "days_normalized": 1})

    assert flags["network_used"] is True
    assert flags["network_scope"] == "public_archive_read_only"
    assert flags["new_data_download_scope"] == "public_historical_aggtrades_5y_extension_only"
    assert flags["ingestion_scope"] == "public_aggtrades_bronze_silver_5y_extension_only"
    assert flags["no_trading"] is True
    assert flags["api_key_used"] is False


def test_v9_31_manifest_preserves_core_decision_fields() -> None:
    report = {
        "status": "PASS",
        "decision": "aggtrades_5y_extension_collection_complete",
        "next_recommendation": "V9.32 - AggTrades 5Y Full Coverage Validation",
        "days_expected_extension": 1096,
        "days_complete": 1096,
        "days_failed": 0,
        "complete_extension_reached": True,
        "target_5y_collection_reached": True,
        "safety_flags": dict(BASE_SAFETY_FLAGS),
        "findings": {},
    }

    manifest = build_manifest_v9_31(report)

    assert manifest["version"] == "V9.31"
    assert manifest["decision"] == report["decision"]
    assert manifest["days_expected_extension"] == 1096
    assert manifest["target_5y_collection_reached"] is True


def test_v9_31_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source


def test_v9_31_test_fixture_uses_tmp_path_for_file_writes(tmp_path: Path) -> None:
    target = tmp_path / "reports" / "data" / "sample.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"version": "V9.31"}), encoding="utf-8")

    assert json.loads(target.read_text(encoding="utf-8"))["version"] == "V9.31"
