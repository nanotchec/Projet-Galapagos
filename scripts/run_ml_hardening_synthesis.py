import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.15.2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({"status": "dry_run_completed"}))
        return

    reports_dir = Path("reports/research")
    version_suffix = args.version.lower().replace(".", "_")

    def _load_report(name: str) -> dict:
        p = reports_dir / f"{name}_{version_suffix}.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    audit = _load_report("ml_leakage_audit")
    baselines = _load_report("ml_random_baselines")
    perms = _load_report("ml_permutation_tests")
    vs_alpha = _load_report("ml_vs_alpha_score")
    _load_report("ml_baseline")

    # Assess leakage
    audit_verdict = audit.get("verdict", "UNKNOWN")
    leakage_risk = audit_verdict != "ML_LEAKAGE_AUDIT_PASSED"

    # We need to compile window-by-window metrics
    windows = {}
    
    # Init windows from permutations
    for r in perms.get("results", []):
        w = r["window"]
        if w not in windows:
            windows[w] = {}
        windows[w]["permutation_passed"] = r.get("permutation", {}).get("verdict") == "ML_PASSES_PERMUTATION_TEST"
        windows[w]["permutation_p_value"] = r.get("permutation", {}).get("p_value_approx")

    # Baselines
    for r in baselines.get("results", []):
        w = r["window"]
        if w not in windows:
            continue
        if "baseline" not in windows[w]:
            windows[w]["baseline_percentiles"] = r.get("baseline", {}).get("distribution_percentiles", {})
            windows[w]["baseline_target_count"] = r.get("target_count")

    # Alpha and top bucket
    for c in vs_alpha.get("comparisons", []):
        w = c["window"]
        if w not in windows:
            continue
        ml_top = c.get("ml_top_10", {})
        alpha_top = c.get("alpha_score_top_10", {})
        
        ml_ret = ml_top.get("cost_adjusted_return", -999)
        alpha_ret = alpha_top.get("cost_adjusted_return", -999)
        
        windows[w]["top_bucket_mean_return"] = ml_top.get("mean_return", 0)
        windows[w]["top_bucket_cost_adjusted"] = ml_ret
        windows[w]["beats_alpha"] = ml_ret > alpha_ret and ml_ret > 0

    # Count passes
    number_of_windows_tested = len(windows)
    windows_passing_permutation = sum(1 for w in windows.values() if w.get("permutation_passed"))
    windows_positive_after_cost = sum(1 for w in windows.values() if w.get("top_bucket_cost_adjusted", -1) > 0)
    windows_beating_alpha_score = sum(1 for w in windows.values() if w.get("beats_alpha"))
    
    # Strict verdict logic
    final_verdict = "ML_NO_EDGE"
    llm_reviewer_ready = False

    if leakage_risk:
        final_verdict = "ML_LEAKAGE_RISK"
    elif number_of_windows_tested < 2:
        final_verdict = "ML_EDGE_NOT_ROBUST"
    else:
        # Check if ALL required conditions are met on AT LEAST 2 windows
        # 1. Leakage audit is already checked
        # 2. Passes permutation on >= 2
        # 3. Beats alpha on >= 2
        # 4. Positive after cost on >= 2
        
        if windows_passing_permutation >= 2 and windows_beating_alpha_score >= 2 and windows_positive_after_cost >= 2:
            final_verdict = "ML_READY_FOR_ENSEMBLE_SIGNALS"
            llm_reviewer_ready = True
        elif windows_passing_permutation >= 1 and windows_positive_after_cost >= 1:
            final_verdict = "ML_REGIME_DEPENDENT_WEAK_EDGE"
        else:
            final_verdict = "ML_FAILS_ROBUSTNESS_CHECKS"

    # Multi-window table output
    table_lines = [
        "| Window | Permutation p-value | Perm Passed | Top Bucket Net Return | Beats Alpha |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for w_name, w_data in sorted(windows.items()):
        p_val = w_data.get("permutation_p_value", "N/A")
        p_pass = w_data.get("permutation_passed", False)
        net_ret = w_data.get("top_bucket_cost_adjusted", 0)
        b_alpha = w_data.get("beats_alpha", False)
        table_lines.append(f"| {w_name} | {p_val} | {p_pass} | {net_ret:.4f} | {b_alpha} |")

    payload = {
        "version": args.version.upper(),
        "final_verdict": final_verdict,
        "leakage_audit": audit_verdict,
        "llm_reviewer_ready": llm_reviewer_ready,
        "number_of_windows_tested": number_of_windows_tested,
        "windows_passing_permutation": windows_passing_permutation,
        "windows_positive_after_cost": windows_positive_after_cost,
        "windows_beating_alpha_score": windows_beating_alpha_score,
        "windows_data": windows,
    }
    
    report_lines = [
        f"Final Verdict: {final_verdict}.",
        f"Leakage Audit: {audit_verdict}.",
        f"LLM reviewer ready: {llm_reviewer_ready}.",
        "",
        "## Window Breakdown",
        *table_lines,
        "",
        "Si LLM reviewer ready est faux, le signal n'est pas robuste sur plusieurs fenetres."
    ]
    
    write_research_report(
        name=f"ml_evaluation_hardening_{version_suffix}",
        payload=payload,
        title=f"ML Evaluation Hardening {args.version.upper()}",
        lines=report_lines,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
