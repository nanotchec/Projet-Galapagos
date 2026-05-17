import json

from galapagos.data.binance_futures_collector import unavailable_derivatives
from galapagos.reports.data_readiness_report import (
    assess_data_readiness,
    generate_data_readiness_report,
)
from galapagos.reports.derivatives_quality_report import generate_derivatives_quality_report


def test_derivatives_snapshot_structure() -> None:
    snapshot = unavailable_derivatives("BTC/USDT:USDT")
    assert snapshot["funding"]["status"] == "unavailable"
    assert "collected_at_utc" in snapshot["open_interest"]
    assert snapshot["liquidations"]["symbol"] == "BTC/USDT:USDT"


def test_derivatives_quality_report_generated(tmp_path) -> None:
    paths = generate_derivatives_quality_report(
        unavailable_derivatives("BTC/USDT:USDT"),
        tmp_path,
    )
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["features"]["funding"] == "unavailable"


def test_data_readiness_report_on_mock_is_degraded(tmp_path) -> None:
    readiness = assess_data_readiness(
        {
            "name": "galapagos_30m",
            "symbol": "BTC/USD",
            "timeframe": "30m",
        },
        use_real_data=False,
    )
    paths = generate_data_readiness_report(readiness, tmp_path)
    assert paths["markdown"].exists()
    assert readiness["status"] in {"READY", "DEGRADED", "NOT_READY"}
    assert readiness["ohlcv_rows"] > 0

