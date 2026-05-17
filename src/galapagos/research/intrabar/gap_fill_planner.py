"""Component to identify gaps in intrabar data and plan fill chunks."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

class GapFillPlanner:
    def __init__(self, timeframe: str = "5min"):
        self.timeframe = timeframe
        self.expected_delta = pd.Timedelta(timeframe)

    def identify_gaps(self, df: pd.DataFrame, target_start: datetime | None = None, target_end: datetime | None = None) -> list[dict[str, Any]]:
        """Find all internal gaps and boundary gaps relative to target window."""
        if df.empty:
            if target_start and target_end:
                 duration = target_end - target_start
                 return [{
                    "start": target_start.isoformat(),
                    "end": target_end.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "duration_str": str(duration),
                    "expected_rows": int(duration / self.expected_delta) - 1
                }]
            return []

        df = df.sort_values("timestamp").copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        
        gaps = []
        
        # Check prefix gap
        if target_start:
            target_start = pd.to_datetime(target_start, utc=True)
            if target_start < df.iloc[0]["timestamp"] - self.expected_delta:
                duration = df.iloc[0]["timestamp"] - target_start
                gaps.append({
                    "start": target_start.isoformat(),
                    "end": df.iloc[0]["timestamp"].isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "duration_str": str(duration),
                    "expected_rows": int(duration / self.expected_delta) - 1
                })

        # Internal gaps
        diffs = df["timestamp"].diff()
        gap_indices = df.index[diffs > self.expected_delta].tolist()
        
        for idx in gap_indices:
            # Finding positional index for gap start/end
            pos = df.index.get_loc(idx)
            start_dt = df.iloc[pos - 1]["timestamp"]
            end_dt = df.iloc[pos]["timestamp"]
            duration = end_dt - start_dt
            
            gaps.append({
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "duration_str": str(duration),
                "expected_rows": int(duration / self.expected_delta) - 1
            })
            
        # Check suffix gap
        if target_end:
            target_end = pd.to_datetime(target_end, utc=True)
            if target_end > df.iloc[-1]["timestamp"] + self.expected_delta:
                duration = target_end - df.iloc[-1]["timestamp"]
                gaps.append({
                    "start": df.iloc[-1]["timestamp"].isoformat(),
                    "end": target_end.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "duration_str": str(duration),
                    "expected_rows": int(duration / self.expected_delta) - 1
                })
                
        return sorted(gaps, key=lambda x: x["duration_seconds"], reverse=True)

    def plan_chunks(self, gap: dict[str, Any], chunk_size_days: int = 7) -> list[dict[str, Any]]:
        """Split a large gap into small manageable chunks."""
        chunks = []
        start_dt = datetime.fromisoformat(gap["start"])
        end_dt = datetime.fromisoformat(gap["end"])
        
        current_dt = start_dt + self.expected_delta
        target_end = end_dt - self.expected_delta
        
        chunk_delta = timedelta(days=chunk_size_days)
        
        while current_dt <= target_end:
            chunk_end = min(current_dt + chunk_delta, target_end)
            chunks.append({
                "start": current_dt.isoformat(),
                "end": chunk_end.isoformat(),
                "status": "planned"
            })
            current_dt = chunk_end + self.expected_delta
            
        return chunks

def generate_gap_fill_plan(
    input_path: str,
    version: str = "v1.22",
    chunk_size_days: int = 7,
    target_start: datetime | None = None,
    target_end: datetime | None = None
) -> dict[str, Any]:
    """Orchestrate gap identification and chunk planning."""
    in_file = Path(input_path)
    if not in_file.exists():
        return {"status": "error", "message": f"File {input_path} not found"}

    df = pd.read_parquet(in_file)
    planner = GapFillPlanner()
    gaps = planner.identify_gaps(df, target_start=target_start, target_end=target_end)
    
    plan = {
        "version": version,
        "input_file": str(in_file),
        "total_rows": len(df),
        "first_timestamp": df["timestamp"].min().isoformat() if not df.empty else None,
        "last_timestamp": df["timestamp"].max().isoformat() if not df.empty else None,
        "gaps_count": len(gaps),
        "all_gaps": gaps,
        "planned_chunks": []
    }
    
    if gaps:
        # Sort chunks by date to avoid jumps
        all_planned_chunks = []
        for gap in gaps:
            all_planned_chunks.extend(planner.plan_chunks(gap, chunk_size_days=chunk_size_days))
            
        plan["planned_chunks"] = sorted(all_planned_chunks, key=lambda x: x["start"])
        plan["status"] = "GAP_FILL_PLAN_READY"
    else:
        plan["status"] = "GAP_FILL_INFEASIBLE_OR_UNNECESSARY"
        plan["message"] = "No gaps found in input data."

    return plan
