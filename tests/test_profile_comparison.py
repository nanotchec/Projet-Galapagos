from galapagos.analysis.profile_comparison import compare_profiles


def test_profile_comparison() -> None:
    result = compare_profiles(
        {
            "galapagos_30m": {"trade_count": 3, "total_pnl": 10},
            "galapagos_4h": {"trade_count": 1, "total_pnl": 4},
        }
    )
    assert result["trade_count_delta_30m_minus_4h"] == 2
    assert result["pnl_delta_30m_minus_4h"] == 6

