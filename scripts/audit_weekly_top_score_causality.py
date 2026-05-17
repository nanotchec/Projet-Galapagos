from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.causality_audit.rule_semantics import analyze_rule_semantics
from galapagos.research.causality_audit.lookahead_detector import detect_selection_lookahead
from galapagos.research.causality_audit.live_executability import audit_live_executability
from galapagos.research.causality_audit.causal_replay import run_causal_replay_comparison
from galapagos.research.causality_audit.verdict_engine import generate_causality_verdict
from galapagos.research.causality_audit.report_writer import save_audit_report

def main():
    parser = argparse.ArgumentParser(description="Audit Weekly Top Score Causality (V1.28)")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--frozen-definition", required=True)
    parser.add_argument("--filter-sweep-report")
    parser.add_argument("--selection-rules-src")
    parser.add_argument("--predictions")
    parser.add_argument("--version", default="v1.28")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Causal Executability Audit ---")
    v_norm = args.version.lower().replace(".", "_")

    # Load inputs
    try:
        with open(args.protocol) as f:
            protocol = json.load(f)
    except Exception as e:
        print(f"Error loading protocol: {e}")
        sys.exit(1)

    try:
        with open(args.frozen_definition) as f:
            frozen_def = json.load(f)
    except Exception as e:
        print(f"Error loading frozen definition: {e}")
        frozen_def = {}

    preds_df = pd.DataFrame()
    if args.predictions and Path(args.predictions).exists():
        try:
            preds_df = pd.read_parquet(args.predictions)
        except Exception as e:
            print(f"Error loading predictions: {e}")

    # 1. Static Audit
    static_res = analyze_rule_semantics(protocol, frozen_def)
    save_audit_report(f"causal_rule_static_audit_{v_norm}", static_res)

    # 2. Lookahead Detection
    lookahead_res = detect_selection_lookahead(preds_df, protocol)
    save_audit_report(f"weekly_top_score_lookahead_audit_{v_norm}", lookahead_res)

    # 3. Live Executability
    exec_res = audit_live_executability(static_res)
    save_audit_report(f"live_executability_audit_{v_norm}", exec_res)

    # 4. Causal Replay
    replay_res = run_causal_replay_comparison(preds_df, protocol)
    save_audit_report(f"causal_replay_comparison_{v_norm}", replay_res)

    # 5. Verdict
    verdict_res = generate_causality_verdict(static_res, lookahead_res, exec_res)
    save_audit_report(f"causal_executability_verdict_{v_norm}", verdict_res)

    # 6. Recommendation
    reco = {
        "final_verdict": verdict_res["final_verdict"],
        "do_not_use_for_live_forward_validation": verdict_res["final_verdict"] == "CURRENT_FILTER_NON_CAUSAL_RETROSPECTIVE_ONLY",
        "existing_evidence_reclassified_as": verdict_res["protocol_status_recommendation"],
        "recommended_next_step": "V1.29 causal cost-aware threshold research" if verdict_res["final_verdict"] == "CURRENT_FILTER_NON_CAUSAL_RETROSPECTIVE_ONLY" else "Continue with current protocol",
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    save_audit_report(f"{v_norm}_recommendation", reco)

    print(f"--- Audit Complete: {verdict_res['final_verdict']} ---")

if __name__ == "__main__":
    main()
