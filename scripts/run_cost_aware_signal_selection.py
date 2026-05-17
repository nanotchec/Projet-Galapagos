from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.report_models import write_research_report
from galapagos.research.signal_selection.candidate_features import build_signal_selection_features
from galapagos.research.signal_selection.confidence_filter_analysis import analyze_confidence
from galapagos.research.signal_selection.filter_sweep import run_filter_sweep
from galapagos.research.signal_selection.frequency_analysis import analyze_frequency
from galapagos.research.signal_selection.leakage_audit import audit_signal_selection_leakage
from galapagos.research.signal_selection.loader import (
    load_selection_inputs,
    read_optional_json,
    reconstruct_policy_results,
)
from galapagos.research.signal_selection.recommendation_engine import (
    build_selection_recommendation,
)
from galapagos.research.signal_selection.regime_filter_analysis import (
    analyze_regime_filters,
)
from galapagos.research.signal_selection.report_models import write_selection_report
from galapagos.research.signal_selection.selection_rules import build_default_rules
from galapagos.research.signal_selection.walk_forward_validation import (
    run_walk_forward_validation,
)
from galapagos.utils.version import display_version, normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="V1.24 Cost-Aware Signal Selection Lab")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--trade-ledger-report", required=True)
    parser.add_argument("--loss-attribution-report", required=True)
    parser.add_argument("--policies", default="fixed_percent,atr_proxy,horizon_only")
    parser.add_argument("--version", default="v1.24")
    parser.add_argument("--random-iterations", type=int, default=500)
    args = parser.parse_args()

    version = normalize_version(args.version)
    display = display_version(version)
    policies = [item.strip() for item in args.policies.split(",") if item.strip()]
    print(f"--- Galapagos {display}: Cost-Aware Signal Selection Lab ---")
    print("Research-only: no Codex CLI, no holdout, no real orders.")

    signals, dataset, intrabar, input_audit = load_selection_inputs(
        predictions_path=args.predictions,
        dataset_path=args.dataset,
        intrabar_path=args.intrabar,
    )
    trade_ledger_report = read_optional_json(args.trade_ledger_report)
    loss_attribution = read_optional_json(args.loss_attribution_report)

    if input_audit.get("status") == "missing_required_inputs":
        payload = {
            "version": display,
            "status": "partial_missing_inputs",
            "input_audit": input_audit,
            "ready_for_reviewer": False,
            "holdout_executed": False,
            "no_real_trading": True,
        }
        write_selection_report(
            stem="signal_selection_summary",
            version=version,
            payload=payload,
            title="Signal Selection Summary",
            lines=[
                "Rapport partiel : des fichiers d'entree manquent.",
                f"Fichiers manquants: {input_audit.get('missing_files', [])}.",
                "Aucun Codex CLI, aucun holdout, aucun ordre reel.",
            ],
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    reconstructed = reconstruct_policy_results(
        signals_df=signals,
        dataset=dataset,
        intrabar=intrabar,
        policies=policies,
    )
    features, feature_audit = build_signal_selection_features(
        signals_df=signals,
        dataset=dataset,
        reconstructed=reconstructed,
    )

    rules = build_default_rules()
    leakage_audit = audit_signal_selection_leakage(
        features=features,
        rules=rules,
        source_paths=[
            Path("src/galapagos/research/signal_selection/candidate_features.py"),
            Path("src/galapagos/research/signal_selection/selection_rules.py"),
        ],
    )
    causal_rules = [rule for rule in rules if rule.causal]
    sweep, random_rows = run_filter_sweep(
        features,
        causal_rules,
        policies=policies,
        iterations=args.random_iterations,
    )
    top_rule_names = _top_causal_rule_names(sweep)
    walk_forward = run_walk_forward_validation(
        features,
        rules=causal_rules,
        policies=["horizon_only"],
        top_rule_names=top_rule_names,
        iterations=args.random_iterations,
    )
    regime = analyze_regime_filters(features, sweep)
    confidence = analyze_confidence(features)
    frequency = analyze_frequency(features)
    recommendation = build_selection_recommendation(
        sweep=sweep,
        confidence_verdicts=confidence["verdicts"],
        regime_verdicts=regime["verdicts"],
        frequency_verdicts=frequency["verdicts"],
        leakage_audit=leakage_audit,
        walk_forward_summary=walk_forward,
    )

    _write_reports(
        version=version,
        display=display,
        features=features,
        feature_audit=feature_audit,
        sweep=sweep,
        random_rows=random_rows,
        regime=regime,
        confidence=confidence,
        frequency=frequency,
        recommendation=recommendation,
        leakage_audit=leakage_audit,
        walk_forward=walk_forward,
        input_audit=input_audit,
        trade_ledger_report=trade_ledger_report,
        loss_attribution=loss_attribution,
        rules=causal_rules,
        policies=policies,
    )
    _update_project_state(version=version, recommendation=recommendation, features=features)
    print(json.dumps(recommendation, indent=2, ensure_ascii=False, default=str))


def _write_reports(
    *,
    version: str,
    display: str,
    features: pd.DataFrame,
    feature_audit: dict[str, Any],
    sweep: list[dict[str, Any]],
    random_rows: list[dict[str, Any]],
    regime: dict[str, Any],
    confidence: dict[str, Any],
    frequency: dict[str, Any],
    recommendation: dict[str, Any],
    leakage_audit: dict[str, Any],
    walk_forward: dict[str, Any],
    input_audit: dict[str, Any],
    trade_ledger_report: dict[str, Any],
    loss_attribution: dict[str, Any],
    rules: list[Any],
    policies: list[str],
) -> None:
    feature_sample = _safe_records(features.head(200))
    feature_rows = _safe_records(features)
    feature_payload = {
        "version": display,
        "rows": int(len(features)),
        "policies": policies,
        "missing_fields": feature_audit.get("missing_fields", []),
        "columns": list(features.columns),
        "feature_sample": feature_sample,
        "feature_rows": feature_rows,
        "input_audit": input_audit,
        "trade_ledger_report_version": trade_ledger_report.get("version"),
        "loss_attribution_keys": list(loss_attribution.keys())[:30],
        "research_only": True,
        "forbidden_future_columns_present": feature_audit.get(
            "forbidden_future_columns_present", []
        ),
        "diagnostic_only_columns": feature_audit.get("diagnostic_only_columns", []),
        "causal_feature_columns": feature_audit.get("causal_feature_columns", []),
    }
    write_selection_report(
        stem="signal_selection_features",
        version=version,
        payload=feature_payload,
        title="Signal Selection Features",
        lines=[
            f"Candidats reconstruits: {len(features)} lignes policy-candidate.",
            f"Policies: {policies}.",
            f"Champs manquants: {feature_payload['missing_fields']}.",
            (
                "Colonnes diagnostic-only: "
                f"{feature_payload['diagnostic_only_columns']}."
            ),
            "Les features sont research-only; elles ne modifient pas les exits.",
        ],
    )

    write_selection_report(
        stem="signal_selection_leakage_audit",
        version=version,
        payload=_json_clean({"version": display, **leakage_audit}),
        title="Signal Selection Leakage Audit",
        lines=[
            f"Statut: {leakage_audit['status']}.",
            f"Verdicts: {leakage_audit['verdicts']}.",
            f"Colonnes futures interdites: {leakage_audit['forbidden_future_columns']}.",
            f"Regles causales: {leakage_audit['causal_rules_count']}.",
            f"Regles diagnostic-only: {leakage_audit['diagnostic_rules_count']}.",
        ],
    )

    sweep_payload = {
        "version": display,
        "filters_tested": len(rules),
        "policies_analyzed": policies,
        "rows": _json_clean(sweep),
        "verdict": recommendation["cost_aware_verdict"],
        "causal_rules_only": True,
    }
    write_selection_report(
        stem="signal_selection_filter_sweep",
        version=version,
        payload=sweep_payload,
        title="Signal Selection Filter Sweep",
        lines=[
            f"Filtres testes: {len(rules)}.",
            f"Policies analysees: {policies}.",
            f"Verdict: {recommendation['cost_aware_verdict']}.",
            "Aucun filtre n'est adopte comme strategie de trading.",
        ],
    )

    random_payload = {
        "version": display,
        "iterations": 500,
        "rows": _json_clean(random_rows),
        "causal_rules_only": True,
    }
    write_selection_report(
        stem="signal_selection_random_baselines",
        version=version,
        payload=random_payload,
        title="Signal Selection Random Baselines",
        lines=[
            "Baseline random same-count avec seed fixe.",
            "Une surperformance sur petit echantillon reste non validee.",
        ],
    )

    for stem, title, payload, lines in [
        (
            "signal_selection_regime_analysis",
            "Signal Selection Regime Analysis",
            {"version": display, **regime},
            [f"Verdicts regime: {regime['verdicts']}."],
        ),
        (
            "signal_selection_confidence_analysis",
            "Signal Selection Confidence Analysis",
            {"version": display, **confidence},
            [f"Verdicts confidence: {confidence['verdicts']}."],
        ),
        (
            "signal_selection_frequency_analysis",
            "Signal Selection Frequency Analysis",
            {"version": display, **frequency},
            [f"Verdicts frequence: {frequency['verdicts']}."],
        ),
    ]:
        write_selection_report(
            stem=stem,
            version=version,
            payload=_json_clean(payload),
            title=title,
            lines=[*lines, "Analyse offline uniquement, sans holdout."],
        )

    write_selection_report(
        stem="signal_selection_walk_forward",
        version=version,
        payload=_json_clean({"version": display, **walk_forward}),
        title="Signal Selection Walk-Forward",
        lines=[
            f"Verdict walk-forward: {walk_forward['walk_forward_verdict']}.",
            f"Fenêtres: {walk_forward['windows']}.",
            "Aucun resultat walk-forward ne valide une strategie a lui seul.",
        ],
    )

    summary_payload = {
        "version": display,
        "filters_tested": len(rules),
        "policies_analyzed": policies,
        "best_filter_observed": recommendation["best_filter_observed"],
        "best_policy_observed": recommendation["best_policy_observed"],
        "selected_count": recommendation["selected_count"],
        "net_mean_pnl_pct": recommendation["net_mean_pnl_pct"],
        "random_same_count_mean": recommendation["random_same_count_mean"],
        "beats_random_p95": recommendation["beats_random_p95"],
        "best_filter_verdict": recommendation["best_filter_verdict"],
        "leakage_audit_status": leakage_audit["status"],
        "walk_forward_verdict": walk_forward["walk_forward_verdict"],
        "leakage_risk_resolved_for_causal_rules": recommendation[
            "leakage_risk_resolved_for_causal_rules"
        ],
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
    }
    write_selection_report(
        stem="signal_selection_summary",
        version=version,
        payload=_json_clean(summary_payload),
        title="Signal Selection Summary",
        lines=[
            (
                "Meilleur filtre observe: "
                f"{summary_payload['best_filter_observed']} "
                f"({summary_payload['best_policy_observed']})."
            ),
            f"Net moyen observe: {summary_payload['net_mean_pnl_pct']}.",
            f"Random same-count mean: {summary_payload['random_same_count_mean']}.",
            f"Walk-forward: {summary_payload['walk_forward_verdict']}.",
            "Reviewer LLM reste desactive.",
        ],
    )

    write_research_report(
        name=f"{version}_recommendation",
        payload=_json_clean({"version": display, **recommendation}),
        title=f"{display} Recommendation",
        lines=[
            f"Cost-aware verdict: {recommendation['cost_aware_verdict']}.",
            (
                "Leakage resolved for causal rules: "
                f"{recommendation['leakage_risk_resolved_for_causal_rules']}."
            ),
            f"Walk-forward verdict: {recommendation['walk_forward_verdict']}.",
            f"Confidence verdicts: {recommendation['confidence_verdicts']}.",
            f"Regime verdicts: {recommendation['regime_verdicts']}.",
            f"Frequency verdicts: {recommendation['frequency_verdicts']}.",
            "ready_for_reviewer = false.",
            "Holdout non execute, aucun ordre reel.",
        ],
    )


def _update_project_state(
    *,
    version: str,
    recommendation: dict[str, Any],
    features: pd.DataFrame,
) -> None:
    display = display_version(version)
    project_state = {
        "version": display,
        "previous_base": "V1.24" if version == "v1_24_1" else "V1.23.1",
        "purpose": "leakage audit + walk-forward validation"
        if version == "v1_24_1"
        else "cost-aware signal selection lab",
        "scientific_verdict": "COST_AWARE_SIGNAL_SELECTION_COMPLETED",
        "continuous_backtest_valid": True,
        "evaluated_ratio": 1.0,
        "features_rows": int(len(features)),
        "best_filter_observed": recommendation["best_filter_observed"],
        "best_policy_observed": recommendation["best_policy_observed"],
        "best_causal_filter": recommendation.get("best_causal_filter"),
        "best_causal_policy": recommendation.get("best_causal_policy"),
        "best_filter_verdict": recommendation["best_filter_verdict"],
        "leakage_audit_status": recommendation.get("leakage_audit_status"),
        "causal_rules_available": True,
        "walk_forward_verdict": recommendation.get("walk_forward_verdict"),
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "holdout_status": "not_executed_locked",
        "codex_cli": "not_called",
        "codex_cli_called": False,
        "no_real_trading": True,
        "real_orders_possible": False,
        "real_trading_possible": False,
    }
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    (reports / "PROJECT_STATE.json").write_text(
        json.dumps(project_state, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (reports / "PROJECT_STATE.md").write_text(
        "\n".join(
            [
                f"# Project State - Galapagos {display}",
                "",
                "## Etat courant",
                f"- Version: {display}.",
                f"- Base precedente: {project_state['previous_base']}.",
                "- Backtest intrabar continu: valide.",
                "- Holdout: non execute et verrouille.",
                "- Codex CLI: non appele.",
                "- Ordres reels: impossibles.",
                "- **Codex CLI** : Non appelé.",
                "- **Holdout** : Non exécuté.",
                "- **Trading Réel** : Désactivé.",
                "- INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER: historique ancien, corrige depuis V1.19+.",
                "",
                "## Verdict scientifique",
                "- COST_AWARE_SIGNAL_SELECTION_COMPLETED.",
                f"- Meilleur filtre observe: {recommendation['best_filter_observed']}.",
                f"- Meilleure policy observee: {recommendation['best_policy_observed']}.",
                f"- Walk-forward: {recommendation.get('walk_forward_verdict')}.",
                f"- Verdict filtre: {recommendation['best_filter_verdict']}.",
                "- Reviewer LLM: desactive.",
                "",
                "## Interpretation",
                f"{display} teste la selection causale de signaux avant toute optimisation d'exit.",
                (
                    "Aucun filtre n'est considere valide pour trading sans "
                    "nouvelle validation offline."
                ),
            ]
        ),
        encoding="utf-8",
    )
    current = reports / "current"
    current.mkdir(exist_ok=True)
    latest_metrics = {
        "version": version.replace("_", "."),
        "scientific_verdict": "COST_AWARE_SIGNAL_SELECTION_COMPLETED",
        "best_filter_observed": recommendation["best_filter_observed"],
        "best_policy_observed": recommendation["best_policy_observed"],
        "selected_count": recommendation["selected_count"],
        "net_mean_pnl_pct": recommendation["net_mean_pnl_pct"],
        "walk_forward_verdict": recommendation.get("walk_forward_verdict"),
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "real_trading_possible": False,
    }
    (current / "latest_metrics.json").write_text(
        json.dumps(_json_clean(latest_metrics), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (current / "latest_summary.md").write_text(
        "\n".join(
            [
                f"# Latest Summary - Galapagos {display}",
                "",
                f"{display} a execute un laboratoire offline de selection cost-aware.",
                (
                    "L'objectif etait de verifier si une reduction de frequence "
                    "peut ameliorer le net apres couts."
                ),
                "",
                f"- Meilleur filtre observe: {recommendation['best_filter_observed']}.",
                f"- Meilleure policy observee: {recommendation['best_policy_observed']}.",
                f"- Walk-forward: {recommendation.get('walk_forward_verdict')}.",
                f"- Verdict: {recommendation['cost_aware_verdict']}.",
                "- Reviewer LLM: desactive.",
                "- Holdout: non execute.",
                "- **Codex CLI** : Non appelé.",
                "- **Holdout** : Non exécuté.",
                "- **Trading Réel** : Désactivé.",
                "- INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER: reference historique; V1.24 utilise le ledger intrabar continu.",
                "- Déduplication: les signaux ML restent dedupliques par timestamp avant evaluation.",
            ]
        ),
        encoding="utf-8",
    )
    _append_report_index(version)
    _append_implementation_report(version, recommendation)


def _append_report_index(version: str) -> None:
    path = Path("reports/REPORT_INDEX.md")
    display = display_version(version)
    suffix = version
    block = "\n".join(
        [
            "",
            f"## {display} - Cost-Aware Signal Selection Lab",
            f"- reports/research/signal_selection_features_{suffix}.md : features de selection.",
            f"- reports/research/signal_selection_filter_sweep_{suffix}.md : sweep des filtres.",
            f"- reports/research/signal_selection_walk_forward_{suffix}.md : walk-forward.",
            f"- reports/research/signal_selection_summary_{suffix}.md : synthese.",
            f"- reports/research/{suffix}_recommendation.md : recommandation scientifique.",
        ]
    )
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Report Index\n"
    if f"## {display} - Cost-Aware Signal Selection Lab" not in existing:
        path.write_text(existing.rstrip() + "\n" + block + "\n", encoding="utf-8")


def _append_implementation_report(version: str, recommendation: dict[str, Any]) -> None:
    path = Path("reports/implementation_report.md")
    display = display_version(version)
    block = "\n".join(
        [
            "",
            f"## {display} - Cost-Aware Signal Selection Lab",
            "- Implementation d'un package `galapagos.research.signal_selection`.",
            "- Reconstruction offline des candidats intrabar par policy sans modifier les exits.",
            f"- Meilleur filtre observe: {recommendation['best_filter_observed']}.",
            f"- Walk-forward: {recommendation.get('walk_forward_verdict')}.",
            f"- Verdict: {recommendation['cost_aware_verdict']}.",
            "- Reviewer LLM desactive, holdout non execute, aucun ordre reel.",
        ]
    )
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Implementation Report\n"
    if f"## {display} - Cost-Aware Signal Selection Lab" not in existing:
        path.write_text(existing.rstrip() + "\n" + block + "\n", encoding="utf-8")


def _top_causal_rule_names(sweep: list[dict[str, Any]]) -> list[str]:
    rows = [
        row
        for row in sweep
        if row.get("causal", True)
        and row.get("rule_name") != "no_trade"
        and row.get("policy") == "horizon_only"
    ]
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("beats_random_p95", False),
            row.get("net_mean_pnl_pct", -999.0),
            row.get("selected_count", 0),
        ),
        reverse=True,
    )
    names = ["low_frequency_strict_score"]
    for row in rows:
        name = row.get("rule_name")
        if name and name not in names:
            names.append(name)
        if len(names) >= 3:
            break
    return names


def _safe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return _json_clean(frame.to_dict("records"))


def _json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value) if not isinstance(value, (list, dict, tuple)) else False:
        return None
    return value


if __name__ == "__main__":
    main()
