"""Component to download klines for identified gaps."""
from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.intrabar.data_sources import INTRABAR_SCHEMA
from galapagos.research.intrabar.downloader import get_binance_klines

logger = logging.getLogger(__name__)

def fill_planned_chunks(
    source: str,
    symbol: str,
    timeframe: str,
    chunks: list[dict[str, Any]],
    max_chunks: int = 48,
    dry_run: bool = False
) -> list[dict[str, Any]]:
    """Download data for each planned chunk."""
    results = []
    
    if source != "binance":
        raise NotImplementedError(f"Download for {source} not yet implemented.")

    for i, chunk in enumerate(chunks):
        if i >= max_chunks:
            logger.warning(f"Max chunks ({max_chunks}) reached. Stopping.")
            break
            
        start_dt = datetime.fromisoformat(chunk["start"])
        end_dt = datetime.fromisoformat(chunk["end"])
        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)
        
        if dry_run:
            results.append({**chunk, "status": "dry_run_success", "rows": 0})
            continue
            
        logger.info(f"Downloading chunk {i+1}/{len(chunks)}: {chunk['start']} to {chunk['end']}")
        chunk_klines = []
        current_ts = start_ts
        try:
            while current_ts < end_ts:
                klines = get_binance_klines(symbol, timeframe, current_ts, end_ts)
                if not klines:
                    break
                chunk_klines.extend(klines)
                current_ts = klines[-1][0] + 1
                time.sleep(0.5) # Respect rate limits
                
            if chunk_klines:
                results.append({**chunk, "status": "success", "rows": len(chunk_klines), "klines": chunk_klines})
            else:
                results.append({**chunk, "status": "failed", "reason": "no data returned"})
        except Exception as e:
            logger.error(f"Download failed for chunk {i+1}: {e}")
            results.append({**chunk, "status": "failed", "reason": str(e)})
        
    return results

def merge_and_save(
    input_path: str,
    output_path: str,
    results: list[dict[str, Any]],
    dry_run: bool = False
) -> pd.DataFrame:
    """Merge downloaded klines with existing data and save."""
    in_file = Path(input_path)
    existing_df = pd.read_parquet(in_file) if in_file.exists() else pd.DataFrame()
    
    new_rows = []
    for r in results:
        if r.get("status") == "success" and "klines" in r:
            new_rows.extend(r["klines"])
            
    if not new_rows:
        return existing_df
        
    new_df = pd.DataFrame(
        new_rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore"
        ]
    )
    new_df["timestamp"] = pd.to_datetime(new_df["open_time"], unit="ms", utc=True)
    new_df["available_timestamp"] = pd.to_datetime(new_df["close_time"], unit="ms", utc=True)
    
    for c in ["open", "high", "low", "close", "volume"]:
        new_df[c] = new_df[c].astype(float)
        
    new_df["source"] = "binance"
    new_df["symbol"] = "BTCUSDT" # Assuming for now
    new_df["timeframe"] = "5m"
    new_df["downloaded_at"] = datetime.now(UTC)
    new_df = new_df[INTRABAR_SCHEMA]
    
    final_df = (
        pd.concat([existing_df, new_df])
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
    )
    
    if not dry_run:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        final_df.to_parquet(output_path, index=False)
        
    return final_df
