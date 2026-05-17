def generate_v1_36_recommendation(summary):
    if summary["final_verdict"] == "CANONICAL_REPRODUCIBLE_UNIVERSE_DEFINED":
        return "rerun EV-net research and reversal diagnostics on canonical reproducible universe"
    else:
        return "resolve universe definition warnings before rerunning EV-net research"
