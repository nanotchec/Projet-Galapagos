def generate_next_steps(mismatch_results):
    primary = mismatch_results.get("primary_mismatch_driver")
    
    if primary == "TRADE_UNIT_MISMATCH":
        return "implement canonical trade universe definition, then rerun V1.32/V1.33 diagnostics"
    elif primary == "JOIN_PATH_MISMATCH":
        return "formalize trade unit and join path before payoff-aware research"
    elif primary == "MISMATCH_UNEXPLAINED":
        return "deep audit EV-net pipeline and trade ledger replay"
    else:
        return "formalize trade unit definition before further research"
