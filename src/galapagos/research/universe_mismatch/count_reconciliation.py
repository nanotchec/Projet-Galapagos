def reconcile_counts(steps_data):
    # steps_data is a list of {step_name, universe_type, count_total, count_2026, explanation}
    reconciliation = []
    prev_count = 0
    prev_2026 = 0
    
    for i, step in enumerate(steps_data):
        delta = step["count_total"] - prev_count if i > 0 else 0
        delta_2026 = step["count_2026"] - prev_2026 if i > 0 else 0
        
        # In V1.34.1, we track comparability
        comparable = step.get("comparable_to_previous", True)
        note = step.get("comparability_note", "")
        
        if not comparable and i > 0:
            delta = 0 # Meaningless if not comparable
            delta_2026 = 0
            if not note:
                note = "Universe change detected, delta not calculated."
        
        reconciliation.append({
            "step_name": step["step_name"],
            "universe_type": step.get("universe_type", "unknown"),
            "total_count": int(step["count_total"]),
            "count_2026": int(step["count_2026"]),
            "delta_from_previous": int(delta),
            "delta_2026": int(delta_2026),
            "comparable_to_previous": comparable,
            "comparability_note": note,
            "explanation": step.get("explanation", "")
        })
        
        prev_count = step["count_total"]
        prev_2026 = step["count_2026"]
        
    return reconciliation
