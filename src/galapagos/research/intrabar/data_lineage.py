"""Logic for inspecting intrabar data lineage."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def inspect_intrabar_lineage(file_path: str, version: str = "v1.20.1") -> dict[str, Any]:
    """Inspect an intrabar parquet file to extract lineage metadata."""
    p = Path(file_path)
    if not p.exists():
        return {
            "status": "error",
            "lineage_status": "INTRABAR_FILE_MISSING",
            "file_exists": False,
            "intrabar_file_path": file_path
        }

    try:
        # We only read the timestamp column to avoid memory overhead for meta-inspection
        df = pd.read_parquet(file_path, columns=["timestamp"])
        rows = len(df)
        first_ts = df["timestamp"].min()
        last_ts = df["timestamp"].max()
        
        inferred_days = 0
        if rows > 0:
            inferred_days = (last_ts - first_ts).total_seconds() / 86400

        # Try to infer symbol/source from path if possible
        # data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_20.parquet
        parts = p.parts
        source = "unknown"
        symbol = "unknown"
        timeframe = "unknown"
        if len(parts) >= 5:
            source = parts[-4]
            symbol = parts[-3]
            timeframe = parts[-2]

        manifest_path = (
            f"data/manifests/intrabar/{source}_{symbol}_{timeframe}_history_manifest.json"
        )
        manifest_exists = Path(manifest_path).exists()

        # Check for gaps
        expected_delta = pd.Timedelta("5min")
        diffs = df["timestamp"].diff().dropna()
        gaps_count = (diffs > expected_delta).sum()
        
        lineage_status = "INTRABAR_LINEAGE_OK"
        if gaps_count > 0:
            lineage_status = "INTRABAR_LINEAGE_OK_WITH_GAPS"

        # Check for download report
        v_norm = version.replace(".", "_")
        if version.startswith("v1.22"):
            download_report_path = f"reports/research/intrabar_gap_fill_download_{v_norm}.json"
        else:
            download_report_path = f"reports/research/intrabar_history_download_{v_norm}.json"
        download_report_exists = Path(download_report_path).exists()

        return {
            "status": "success",
            "lineage_status": lineage_status,
            "intrabar_file_path": str(p.resolve()),
            "file_exists": True,
            "rows": rows,
            "gaps_count": int(gaps_count),
            "first_timestamp": (
                first_ts.isoformat() 
                if hasattr(first_ts, "isoformat") 
                else str(first_ts)
            ),
            "last_timestamp": (
                last_ts.isoformat() 
                if hasattr(last_ts, "isoformat") 
                else str(last_ts)
            ),
            "inferred_days": round(inferred_days, 2),
            "source": source,
            "symbol": symbol,
            "timeframe": timeframe,
            "manifest_exists": manifest_exists,
            "manifest_path": manifest_path,
            "download_report_exists": download_report_exists,
            "download_report_path": download_report_path,
        }
    except Exception as e:
        return {
            "status": "error",
            "lineage_status": "INTRABAR_LINEAGE_INCONSISTENT",
            "message": str(e),
            "intrabar_file_path": file_path
        }
