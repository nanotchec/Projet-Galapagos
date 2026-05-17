import hashlib
import json
import pandas as pd

def generate_universe_fingerprint(df, definition, version):
    # Sample and hash to get data fingerprint
    # For stability, use a sample or summary
    row_count = len(df)
    min_ts = str(df["timestamp"].min())
    max_ts = str(df["timestamp"].max())
    
    # Hash of canonical keys (sorted)
    keys_sample = df["timestamp"].astype(str).sort_values().head(1000).to_string()
    key_hash = hashlib.sha256(keys_sample.encode()).hexdigest()
    
    # Definition hash
    def_json = json.dumps(definition, sort_keys=True)
    def_hash = hashlib.sha256(def_json.encode()).hexdigest()
    
    # Final fingerprint
    final_input = f"{key_hash}_{def_hash}_{version}"
    fingerprint = hashlib.sha256(final_input.encode()).hexdigest()
    
    return {
        "universe_fingerprint": fingerprint,
        "definition_fingerprint": def_hash,
        "canonical_key_hash": key_hash,
        "rows_count": row_count,
        "min_timestamp": min_ts,
        "max_timestamp": max_ts,
        "fingerprint_status": "CANONICAL_UNIVERSE_FINGERPRINT_CREATED"
    }
