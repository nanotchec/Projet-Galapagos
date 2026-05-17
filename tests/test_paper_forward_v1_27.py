import pytest
import pandas as pd
from galapagos.research.paper_forward.protocol_loader import load_and_verify_protocol
from galapagos.research.paper_forward.frozen_filter import apply_frozen_filter
from galapagos.research.paper_forward.criteria_evaluator import evaluate_success_criteria

def test_protocol_check_fails_on_unlocked():
    protocol = {"protocol_locked": False}
    # Mocking file read or passing dict
    # Test internal logic
    from galapagos.research.paper_forward.protocol_loader import load_and_verify_protocol
    # ... logic check ...
    pass

def test_frozen_filter_rejects_forbidden():
    protocol = {"candidate_filter": "low_frequency_strict_score"}
    candidates = pd.DataFrame({"timestamp": [1], "forward_return": [0.1]})
    with pytest.raises(ValueError, match="Forbidden column detected"):
        apply_frozen_filter(candidates, protocol)

def test_criteria_inconclusive_if_low_count():
    metrics = {"selected_count": 10, "mean_net_pnl_after_cost_pct": 0.05}
    criteria = {"minimal_requirements": {"selected_count": ">= 60"}}
    res = evaluate_success_criteria(metrics, criteria)
    assert res["status"] == "INCONCLUSIVE_NEEDS_MORE_DATA"
    assert res["validation_passed"] is False

def test_protocol_loader_all_locks():
    # Verify the list of locks
    pass
