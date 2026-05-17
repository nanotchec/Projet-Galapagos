from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def write_anti_overfit_summary(
    *,
    evaluation_run_id: str,
    config: dict[str, Any],
    window_results: list[dict[str, Any]],
    output_dir: str | Path,
    holdout_executed: bool,
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = build_anti_overfit_summary(
        evaluation_run_id=evaluation_run_id,
        config=config,
        window_results=window_results,
        holdout_executed=holdout_executed,
    )
    md_path = directory / "anti_overfit_summary.md"
    json_path = directory / "anti_overfit_summary.json"
    md_path.write_text(_markdown(payload), encoding="utf-8")
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


def build_anti_overfit_summary(
    *,
    evaluation_run_id: str,
    config: dict[str, Any],
    window_results: list[dict[str, Any]],
    holdout_executed: bool,
) -> dict[str, Any]:
    gpt_metrics = [
        result.get("gpt_setup_review", {})
        for result in window_results
        if result.get("gpt_setup_review", {}).get("executed")
    ]
    pnl_values = [float(item.get("net_pnl") or 0.0) for item in gpt_metrics]
    verdict = _verdict(window_results, gpt_metrics, holdout_executed)
    return {
        "evaluation_run_id": evaluation_run_id,
        "evaluation_name": config.get("evaluation_name"),
        "profile": config.get("profile"),
        "asset": config.get("asset"),
        "timeframe": config.get("timeframe"),
        "holdout_executed": holdout_executed,
        "windows": window_results,
        "stability": {
            "gpt_windows_executed": len(gpt_metrics),
            "net_pnl_mean": mean(pnl_values) if pnl_values else None,
            "net_pnl_std": pstdev(pnl_values) if len(pnl_values) > 1 else 0.0,
            "warning": (
                "Resultat positif isole: insuffisant pour conclure."
                if len([value for value in pnl_values if value > 0]) == 1
                else None
            ),
        },
        "verdict": verdict,
        "anti_overfit_warning": (
            "Ne pas modifier le prompt apres avoir regarde le holdout, "
            "sauf a creer un nouveau holdout."
        ),
        "safety": "Le systeme V1.9 ne peut toujours pas passer d'ordre reel.",
    }


def _verdict(
    window_results: list[dict[str, Any]],
    gpt_metrics: list[dict[str, Any]],
    holdout_executed: bool,
) -> str:
    if not gpt_metrics:
        return "NOT_ENOUGH_DATA"
    pnl_values = [float(item.get("net_pnl") or 0.0) for item in gpt_metrics]
    if len(gpt_metrics) < len(window_results):
        return "NOT_ENOUGH_DATA"
    if any(value < 0 for value in pnl_values) and any(value > 0 for value in pnl_values):
        return "UNSTABLE"
    if all(value < 0 for value in pnl_values):
        return "FAILS_BASELINES"
    if not holdout_executed:
        return "PROMISING_BUT_UNVALIDATED"
    return "READY_FOR_FORWARD_PAPER_SMALL"


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Evaluation anti-overfit Galapagos - {payload['evaluation_run_id']}",
        "",
        "## Synthese",
        f"- Evaluation : {payload.get('evaluation_name')}",
        f"- Profil : {payload.get('profile')}",
        f"- Actif : {payload.get('asset')}",
        f"- Timeframe : {payload.get('timeframe')}",
        f"- Holdout execute : {payload.get('holdout_executed')}",
        f"- Verdict : {payload.get('verdict')}",
        "",
        "## Fenetres",
    ]
    for result in payload.get("windows", []):
        window = result.get("window", {})
        lines.extend(
            [
                f"### {result.get('window_label')}",
                f"- Index : {window.get('start_index')} -> {window.get('end_index')}",
                f"- Periode : {window.get('start_timestamp')} -> {window.get('end_timestamp')}",
                f"- Bougies : {window.get('bars')}",
                f"- Candidats trouves : {result.get('candidates_found')}",
                f"- Candidats soumis GPT : {result.get('gpt_setup_review', {}).get('submitted')}",
                f"- Ledger PnL matches official : {result.get('ledger_pnl_matches_official')}",
                f"- Baselines : {list((result.get('baselines') or {}).keys())}",
            ]
        )
    lines.extend(
        [
            "",
            "## Stabilite",
            json.dumps(payload.get("stability", {}), indent=2, ensure_ascii=False),
            "",
            "## Avertissement",
            payload["anti_overfit_warning"],
            payload["safety"],
        ]
    )
    return "\n".join(lines)
