def score_hypotheses(replays, target_count_2026):
    scorecard = []
    
    for r in replays:
        count_2026 = r["count_2026"]
        delta = count_2026 - target_count_2026
        pct_delta = abs(delta) / target_count_2026 if target_count_2026 > 0 else 1.0
        
        match_status = "REPLAY_NOT_MATCHING"
        if delta == 0:
            match_status = "REPLAY_MATCHES_SOURCE"
        elif pct_delta < 0.01:
            match_status = "REPLAY_CLOSE_TO_SOURCE"
            
        scorecard.append({
            "hypothesis_id": r["hypothesis_id"],
            "count_2026": count_2026,
            "target_count_2026": target_count_2026,
            "delta": delta,
            "pct_delta": pct_delta,
            "match_status": match_status,
            "replay_status": r.get("replay_status"),
            "ev_proxy_available": r.get("ev_proxy_available"),
            "cost_proxy_available": r.get("cost_proxy_available")
        })
        
    return scorecard
