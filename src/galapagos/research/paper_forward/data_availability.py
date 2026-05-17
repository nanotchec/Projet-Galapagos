from __future__ import annotations

import pyarrow.parquet as pq
from pathlib import Path
from typing import Any
import pandas as pd

def check_data_availability(
    predictions_path: str,
    dataset_path: str,
    intrabar_path: str,
    reference_end_timestamp: str = "2026-05-06T20:35:00Z"
) -> dict[str, Any]:
    """Check if new out-of-sample data is available with dynamic timestamp detection."""
    
    sources = {
        "predictions": predictions_path,
        "dataset": dataset_path,
        "intrabar": intrabar_path
    }
    
    results = {
        "reference_end_timestamp": reference_end_timestamp,
        "max_timestamps": {},
        "timestamp_column_used": {},
        "source_read_status": {},
        "has_new_out_of_sample_data": False,
        "out_of_sample_duration_days": 0,
        "true_out_of_sample_possible": False
    }
    
    ref_ts = pd.to_datetime(reference_end_timestamp).tz_localize(None)
    overall_max_ts = ref_ts
    
    # Ordered preference for timestamp columns
    ts_candidates = ["timestamp", "open_time", "available_timestamp", "close_time"]
    
    for key, path in sources.items():
        p = Path(path)
        if not p.exists():
            results["source_read_status"][key] = "FILE_MISSING"
            continue
            
        try:
            # Inspect schema to find the best timestamp column without reading the whole file
            parquet_file = pq.ParquetFile(path)
            schema_names = parquet_file.schema.names
            
            found_col = None
            for cand in ts_candidates:
                if cand in schema_names:
                    found_col = cand
                    break
            
            if not found_col:
                results["source_read_status"][key] = "TIMESTAMP_COLUMN_MISSING"
                continue
            
            results["timestamp_column_used"][key] = found_col
            
            # Read only the found column
            df = pd.read_parquet(path, columns=[found_col])
            max_ts = df[found_col].max()
            
            if not isinstance(max_ts, pd.Timestamp):
                max_ts = pd.to_datetime(max_ts)
            
            # Normalize to naive
            if max_ts.tz is not None:
                max_ts = max_ts.tz_localize(None)
            
            results["max_timestamps"][key] = max_ts.isoformat()
            results["source_read_status"][key] = "READ_OK"
            
            if max_ts > overall_max_ts:
                overall_max_ts = max_ts
                
        except Exception as e:
            results["source_read_status"][key] = f"READ_ERROR: {str(e)}"
            
    if overall_max_ts > ref_ts:
        results["has_new_out_of_sample_data"] = True
        results["true_out_of_sample_possible"] = True
        duration = overall_max_ts - ref_ts
        results["out_of_sample_duration_days"] = duration.total_seconds() / 86400
        
    results["status"] = "OUT_OF_SAMPLE_DATA_DETECTED" if results["has_new_out_of_sample_data"] else "NO_NEW_OUT_OF_SAMPLE_DATA"
    
    # Final check: if critical source is missing
    critical_sources = ["predictions", "intrabar"]
    missing_critical = [s for s in critical_sources if results["source_read_status"].get(s) != "READ_OK"]
    if missing_critical:
        results["status"] = "DATA_INPUTS_PARTIAL"
        
    return results
