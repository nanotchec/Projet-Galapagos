def analyze_matches(scorecard):
    valid_replays = [x for x in scorecard if x.get("replay_status") == "REPLAY_COMPLETE"]
    
    if not valid_replays:
        return {
            "best_source_match_hypothesis": "none",
            "best_source_match_count": 0,
            "best_source_match_delta": 0,
            "any_exact_source_match": False,
            "any_close_source_match": False,
            "source_match_confidence": "NONE",
            "match_analysis_status": "SOURCE_PATH_REPLAY_INVALID",
            "valid_ev_replay_count": 0
        }
        
    best_match = min(valid_replays, key=lambda x: abs(x["delta"]))
    
    any_exact = any(x["match_status"] == "REPLAY_MATCHES_SOURCE" for x in valid_replays)
    any_close = any(x["match_status"] == "REPLAY_CLOSE_TO_SOURCE" for x in valid_replays)
    
    status = "SOURCE_PATH_NOT_RECOVERED_AFTER_VALID_EV_REPLAY"
    confidence = "LOW"
    
    if any_exact:
        status = "EXACT_SOURCE_PATH_RECOVERED"
        confidence = "HIGH"
    elif any_close:
        status = "CLOSE_SOURCE_PATH_RECOVERED"
        confidence = "MEDIUM"
        
    return {
        "best_source_match_hypothesis": best_match["hypothesis_id"],
        "best_source_match_count": best_match["count_2026"],
        "best_source_match_delta": best_match["delta"],
        "any_exact_source_match": any_exact,
        "any_close_source_match": any_close,
        "source_match_confidence": confidence,
        "match_analysis_status": status,
        "valid_ev_replay_count": len(valid_replays)
    }
