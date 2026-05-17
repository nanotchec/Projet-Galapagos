import pytest
from galapagos.research.source_path_reconstruction.candidate_path_generator import generate_hypotheses
from galapagos.research.source_path_reconstruction.path_scorecard import score_hypotheses
from galapagos.research.source_path_reconstruction.source_match_analyzer import analyze_matches
from galapagos.research.source_path_reconstruction.non_reproducibility_classifier import classify_non_reproducibility

def test_hypotheses_generation():
    hypotheses = generate_hypotheses()
    assert len(hypotheses) > 0
    ids = [h["id"] for h in hypotheses]
    assert len(ids) == len(set(ids)) # Unique IDs

def test_scorecard_exact_match():
    replays = [
        {"hypothesis_id": "H1", "count_2026": 12691}
    ]
    scorecard = score_hypotheses(replays, 12691)
    assert scorecard[0]["match_status"] == "REPLAY_MATCHES_SOURCE"
    assert scorecard[0]["delta"] == 0

def test_scorecard_no_match():
    replays = [
        {"hypothesis_id": "H1", "count_2026": 8939}
    ]
    scorecard = score_hypotheses(replays, 12691)
    assert scorecard[0]["match_status"] == "REPLAY_NOT_MATCHING"
    assert scorecard[0]["delta"] != 0

def test_analyze_exact_match():
    scorecard = [
        {"hypothesis_id": "H1", "count_2026": 12691, "delta": 0, "match_status": "REPLAY_MATCHES_SOURCE", "replay_status": "REPLAY_COMPLETE"}
    ]
    analysis = analyze_matches(scorecard)
    assert analysis["any_exact_source_match"] is True
    assert analysis["match_analysis_status"] == "EXACT_SOURCE_PATH_RECOVERED"

def test_replay_fails_without_ev():
    from galapagos.research.source_path_reconstruction.path_replay_engine import replay_hypothesis
    import pandas as pd
    df = pd.DataFrame({"predicted_probability": [0.7]}, index=pd.to_datetime(["2026-01-01"]))
    df.index.name = "timestamp"
    
    hypothesis = {"id": "H1", "join_policy": "none", "warmup_policy": "none", "outcome_policy": "none", "dedup_policy": "none"}
    result = replay_hypothesis(hypothesis, df, pd.DataFrame())
    
    assert result["replay_status"] == "REPLAY_FAILED_MISSING_EV_PROXY"
    assert result["count_2026"] == 0
    assert result["fallback_used"] is False

def test_classify_non_repro_insufficient_artifacts():
    analysis = {"any_exact_source_match": False}
    audit = {"status": "SOURCE_ARTIFACTS_PARTIALLY_RECONSTRUCTABLE"}
    inspection = {"potential_count_affecting_changes": []}
    
    result = classify_non_reproducibility(analysis, inspection, audit)
    assert result["status"] == "SOURCE_PATH_NOT_RECOVERED_FROM_AVAILABLE_ARTIFACTS"
    assert result["primary_non_reproducibility_driver"] == "SOURCE_ARTIFACTS_INSUFFICIENT"

def test_hypothesis_diversity_collapse():
    from galapagos.research.source_path_reconstruction.hypothesis_diversity import analyze_hypothesis_diversity
    replays = [
        {"hypothesis_id": "H1", "count_2026": 8939, "replay_status": "REPLAY_COMPLETE"},
        {"hypothesis_id": "H2", "count_2026": 8939, "replay_status": "REPLAY_COMPLETE"},
        {"hypothesis_id": "H3", "count_2026": 8939, "replay_status": "REPLAY_COMPLETE"},
        {"hypothesis_id": "H4", "count_2026": 5000, "replay_status": "REPLAY_COMPLETE"},
        {"hypothesis_id": "H5", "count_2026": 6000, "replay_status": "REPLAY_COMPLETE"},
        {"hypothesis_id": "H6", "count_2026": 8939, "replay_status": "REPLAY_COMPLETE"},
    ]
    result = analyze_hypothesis_diversity(replays)
    assert result["hypothesis_diversity_status"] == "HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT"
    assert result["dominant_replay_count_2026"] == 8939
    assert result["dominant_replay_count_frequency"] == 4
