def generate_hypotheses():
    hypotheses = []
    
    # H1: Raw Prediction Rows (No Join)
    hypotheses.append({
        "id": "H1",
        "name": "raw_predictions_no_join",
        "universe_unit": "raw_row",
        "join_policy": "none",
        "dedup_policy": "none",
        "warmup_policy": "none",
        "outcome_policy": "none",
        "expected_effect": "very_high_count"
    })
    
    # H2: Joined Inner
    hypotheses.append({
        "id": "H2",
        "name": "joined_inner",
        "universe_unit": "raw_row",
        "join_policy": "inner",
        "dedup_policy": "none",
        "warmup_policy": "none",
        "outcome_policy": "none",
        "expected_effect": "high_count"
    })
    
    # H3: Joined Inner + Warmup 100
    hypotheses.append({
        "id": "H3",
        "name": "joined_inner_warmup_100",
        "universe_unit": "raw_row",
        "join_policy": "inner",
        "dedup_policy": "none",
        "warmup_policy": "100_bars",
        "outcome_policy": "none",
        "expected_effect": "medium_count"
    })
    
    # H4: Joined Inner + Warmup 100 + Outcome Available
    hypotheses.append({
        "id": "H4",
        "name": "joined_inner_warmup_100_outcome_only",
        "universe_unit": "raw_row",
        "join_policy": "inner",
        "dedup_policy": "none",
        "warmup_policy": "100_bars",
        "outcome_policy": "outcome_present",
        "expected_effect": "lower_count"
    })
    
    # H5: Dedup Timestamp (Current Rebuild)
    hypotheses.append({
        "id": "H5",
        "name": "dedup_timestamp_rebuild",
        "universe_unit": "unique_timestamp",
        "join_policy": "inner",
        "dedup_policy": "first_row",
        "warmup_policy": "100_bars",
        "outcome_policy": "none",
        "expected_effect": "lowest_count"
    })

    # H6: All Models Selection (36 rows per ts)
    hypotheses.append({
        "id": "H6",
        "name": "all_models_selection",
        "universe_unit": "raw_row",
        "join_policy": "inner",
        "dedup_policy": "none",
        "warmup_policy": "none",
        "outcome_policy": "none",
        "expected_effect": "high_count"
    })
    
    return hypotheses
