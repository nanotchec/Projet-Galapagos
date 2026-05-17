"""Improved intrabar data downloader for historical extension."""
from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.intrabar.data_sources import INTRABAR_SCHEMA
from galapagos.research.intrabar.downloader import get_binance_klines

logger = logging.getLogger(__name__)

def extend_history(
    source: str,
    symbol: str,
    timeframe: str,
    days: int,
    output_path: str,
    max_chunks: int = 12,
    dry_run: bool = False,
    version: str = "v1.20"
) -> dict[str, Any]:
    """Download and extend historical intrabar data."""
    if source != "binance":
        raise NotImplementedError(f"Download for {source} not yet implemented.")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_dir = Path("data/manifests/intrabar")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{source}_{symbol}_{timeframe}_history_manifest.json"

    if dry_run:
        return {
            "status": "dry_run",
            "source": source,
            "symbol": symbol,
            "timeframe": timeframe,
            "requested_days": days,
            "output_path": str(out_file),
            "manifest_path": str(manifest_path)
        }

    # Determine range
    now = datetime.now(UTC)
    end_dt = now
    start_dt = end_dt - timedelta(days=days)
    
    # Check if we already have some data
    existing_df = pd.DataFrame()
    if out_file.exists():
        try:
            existing_df = pd.read_parquet(out_file)
            if not existing_df.empty:
                existing_df["timestamp"] = pd.to_datetime(existing_df["timestamp"], utc=True)
                existing_df["timestamp"].min()
                curr_max = existing_df["timestamp"].max()
                
                # If we have a gap at the end (forwards)
                if curr_max < end_dt - timedelta(hours=1):
                    # We can try to download from curr_max to end_dt
                    # But the current logic only does one pass. 
                    # For V1.21, let's just make sure we cover the requested days.
                    pass
        except Exception as e:
            logger.warning(f"Failed to read existing file: {e}. Starting fresh.")

    # Simpler logic for V1.21: 
    # 1. Download the requested range [now - days, now]
    # 2. Merge with existing
    # 3. Save
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    all_klines = []
    current_ts = start_ts
    chunks_count = 0
    
    while current_ts < end_ts and chunks_count < max_chunks:
        # Avoid downloading what we already have if it's a lot
        if not existing_df.empty:
            # If current_ts is within existing range, skip to end of existing range
            curr_dt = pd.to_datetime(current_ts, unit="ms", utc=True)
            in_range = (curr_dt >= existing_df["timestamp"].min() and 
                        curr_dt < existing_df["timestamp"].max())
            if in_range:
                current_ts = int(existing_df["timestamp"].max().timestamp() * 1000) + 1
                continue

        try:
            klines = get_binance_klines(symbol, timeframe, current_ts, end_ts)
            if not klines:
                break
            
            all_klines.extend(klines)
            current_ts = klines[-1][0] + 1
            chunks_count += 1
            time.sleep(0.5)  # Rate limit
        except Exception as e:
            logger.error(f"Download error at {current_ts}: {e}")
            break

    if not all_klines and existing_df.empty:
        return {"status": "failed", "reason": "no data returned"}

    new_df = pd.DataFrame()
    if all_klines:
        new_df = pd.DataFrame(
            all_klines,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore"
            ]
        )
        new_df["timestamp"] = pd.to_datetime(new_df["open_time"], unit="ms", utc=True)
        new_df["available_timestamp"] = pd.to_datetime(new_df["close_time"], unit="ms", utc=True)
        
        for c in ["open", "high", "low", "close", "volume"]:
            new_df[c] = new_df[c].astype(float)
            
        new_df["source"] = source
        new_df["symbol"] = symbol
        new_df["timeframe"] = timeframe
        new_df["downloaded_at"] = datetime.now(UTC)
        new_df = new_df[INTRABAR_SCHEMA]

    # Combine with existing
    final_df = (
        pd.concat([existing_df, new_df])
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
    )
    
    if not dry_run:
        final_df.to_parquet(out_file, index=False)

    # Update manifest
    manifest = {
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "days_requested": days,
        "start_time": final_df["timestamp"].min().isoformat(),
        "end_time": final_df["timestamp"].max().isoformat(),
        "rows": len(final_df),
        "chunks_successful": chunks_count,
        "version": version,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if not dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "status": "INTRABAR_HISTORY_EXTENDED" if chunks_count > 0 else "INTRABAR_HISTORY_UNCHANGED",
        "existing_file_reused": not existing_df.empty,
        "merge_performed": not new_df.empty and not existing_df.empty,
        "rows": len(final_df),
        "first_timestamp": final_df["timestamp"].min().isoformat(),
        "last_timestamp": final_df["timestamp"].max().isoformat(),
        "file_path": str(out_file),
        "manifest_path": str(manifest_path),
        "chunks_successful": chunks_count,
        "dry_run": dry_run
    }
