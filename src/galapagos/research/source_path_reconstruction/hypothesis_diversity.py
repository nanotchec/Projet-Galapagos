def analyze_hypothesis_diversity(replays):
    counts_2026 = [r["count_2026"] for r in replays if r.get("replay_status") == "REPLAY_COMPLETE"]
    
    if not counts_2026:
        return {
            "hypothesis_diversity_status": "HYPOTHESES_INVALID",
            "unique_2026_counts": [],
            "repeated_count_groups": {}
        }
        
    unique_counts = sorted(list(set(counts_2026)))
    counts_freq = {c: counts_2026.count(c) for c in unique_counts}
    
    dominant_count = max(counts_freq, key=counts_freq.get)
    dominant_freq = counts_freq[dominant_count]
    
    status = "HYPOTHESES_DIVERSE"
    # Rule: If dominant count is the rebuild count (8939) and occurs in at least half of valid replays
    if dominant_count == 8939 and (dominant_freq / len(counts_2026)) >= 0.5:
        status = "HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT"
    elif len(unique_counts) == 1:
        status = "HYPOTHESES_LOW_DISCRIMINATION"
    elif dominant_freq / len(counts_2026) > 0.7:
        status = "HYPOTHESES_LOW_DISCRIMINATION"
        
    return {
        "hypotheses_tested_count": len(replays),
        "unique_2026_counts": unique_counts,
        "repeated_count_groups": counts_freq,
        "dominant_replay_count_2026": dominant_count,
        "dominant_replay_count_frequency": dominant_freq,
        "hypothesis_diversity_status": status
    }
