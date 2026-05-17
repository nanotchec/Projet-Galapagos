from __future__ import annotations

import pandas as pd
import pytest

from galapagos.research.ev_net_research.recommendation_engine import generate_v1_32_recommendation


def test_verdict_negative_2026_pnl():
    # Even if other metrics are good, negative 2026 pnl should trigger RECENT_WINDOW_NEGATIVE
    summary = {
        "best_filter_observed": "filter_test",
        "eligible_filters_count": 1,
        "recent_2026_selected_count": 100,
        "recent_2026_pnl": -0.001,
        "active_windows_count": 5,
        "beats_monthly_random_p95": True,
        "rows_blocked_by_warmup_count": 0
    }
    
    recs = generate_v1_32_recommendation(summary)
    assert recs["final_verdict"] == "EV_NET_RESEARCH_RECENT_WINDOW_NEGATIVE"


def test_verdict_promising_requires_positive_pnl():
    summary = {
        "best_filter_observed": "filter_test",
        "eligible_filters_count": 1,
        "recent_2026_selected_count": 100,
        "recent_2026_pnl": 0.001,
        "active_windows_count": 5,
        "beats_monthly_random_p95": True,
        "rows_blocked_by_warmup_count": 0
    }
    
    recs = generate_v1_32_recommendation(summary)
    assert recs["final_verdict"] == "EV_NET_RESEARCH_PROMISING_BUT_UNVALIDATED"


def test_verdict_no_signals_2026():
    summary = {
        "best_filter_observed": "filter_test",
        "eligible_filters_count": 1,
        "recent_2026_selected_count": 0,
        "recent_2026_pnl": 0.0,
        "active_windows_count": 4,
        "beats_monthly_random_p95": True,
        "rows_blocked_by_warmup_count": 0
    }
    
    recs = generate_v1_32_recommendation(summary)
    assert recs["final_verdict"] == "EV_NET_RESEARCH_RECENT_WINDOW_NO_SIGNALS"
