from __future__ import annotations

from galapagos.research.derivatives_source_readiness_v9_52 import decide_source_readiness_v9_52


def test_v9_52_decision_accepts_funding_and_limited_oi():
    decision = decide_source_readiness_v9_52(
        {"readiness_decision": "funding_ready_for_public_archive_probe_and_collection"},
        {"readiness_decision": "oi_not_ready_history_limited"},
    )

    assert decision == "derivatives_source_readiness_funding_ready_oi_limited"


def test_v9_52_decision_blocks_uncertain_funding():
    decision = decide_source_readiness_v9_52(
        {"readiness_decision": "funding_uncertain"},
        {"readiness_decision": "oi_not_ready_history_limited"},
    )

    assert decision == "derivatives_source_readiness_not_ready_source_uncertainty"
