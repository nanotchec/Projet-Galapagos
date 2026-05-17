from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from galapagos.backtest.candidate_selector import (
    CandidateSetup,
    candidate_to_dict,
    select_candidate_setups_from_data,
)
from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.holdout_guard import mark_holdout_used, stable_hash
from galapagos.evaluation.window_selector import (
    EvaluationWindow,
    ensure_no_overlap,
    split_ohlcv_into_windows,
)
from galapagos.reports.anti_overfit_report import write_anti_overfit_summary
from galapagos.utils.config_loader import load_profile, load_yaml

SUPPORTED_MODES = {"dry-run", "calibration", "validation", "holdout", "all"}


def run_anti_overfit_evaluation(
    *,
    config_path: str | Path,
    mode: str = "dry-run",
    allow_codex_cli: bool = False,
    output_root: str | Path = "reports/evaluation",
    cache_options: dict[str, bool] | None = None,
) -> dict[str, Any]:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported evaluation mode: {mode}")
    if mode != "dry-run" and not allow_codex_cli:
        raise RuntimeError(f"Mode {mode} requires --allow-codex-cli.")

    config = load_yaml(config_path)
    profile = load_profile(str(config.get("profile", "galapagos_4h")))
    if profile.get("timeframe") != "4h":
        raise RuntimeError("V1.9 anti-overfit evaluation is limited to profile 4h.")

    data_path = _find_best_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found. Run download_historical_ohlcv first.")
    data = load_historical_ohlcv(data_path).sort_values("timestamp").drop_duplicates("timestamp")
    windows = _named_windows(config, data)
    selected_labels = _selected_labels(mode)
    selected_windows = [window for window in windows if window.label in selected_labels]
    if not selected_windows:
        raise RuntimeError(f"No evaluation windows selected for mode {mode}.")

    evaluation_run_id = (
        f"{config.get('evaluation_name', 'anti_overfit')}_"
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_"
        f"{str(uuid4())[:8]}"
    )
    output_dir = Path(output_root) / evaluation_run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == "holdout":
        mark_holdout_used(
            output_dir,
            config_hash=stable_hash(config),
            prompt_hash=stable_hash({"prompt_mode": "setup_review", "version": "V1.9"}),
        )

    window_results = []
    for window in selected_windows:
        if mode == "dry-run":
            result = _run_window_dry(
                window=window,
                config=config,
                profile=profile,
                data=data,
                output_dir=output_dir,
                data_path=data_path,
                codex_planned=False,
            )
        else:
            result = _run_window_codex(
                window=window,
                config=config,
                config_path=Path(config_path),
                data=data,
                output_dir=output_dir,
                data_path=data_path,
                cache_options=cache_options or {},
            )
        window_results.append(result)
    summary_paths = write_anti_overfit_summary(
        evaluation_run_id=evaluation_run_id,
        config=config,
        window_results=window_results,
        output_dir=output_dir,
        holdout_executed=mode == "holdout",
    )
    return {
        "evaluation_run_id": evaluation_run_id,
        "mode": mode,
        "config_path": str(config_path),
        "data_path": str(data_path),
        "output_dir": str(output_dir),
        "summary_paths": {key: str(value) for key, value in summary_paths.items()},
        "windows": window_results,
        "holdout_executed": mode == "holdout",
        "codex_cli_called": mode != "dry-run",
        "safety": "Le systeme V1.9 ne peut toujours pas passer d'ordre reel.",
    }


def _named_windows(config: dict[str, Any], data: pd.DataFrame) -> list[EvaluationWindow]:
    window_config = config.get("windows") or {}
    labels = [str(payload.get("label") or key) for key, payload in window_config.items()]
    min_bars = int(config.get("min_bars_per_window", 80))
    base_windows = split_ohlcv_into_windows(data, len(labels), min_bars)
    windows = [
        EvaluationWindow(
            label=label,
            start_index=base.start_index,
            end_index=base.end_index,
            start_timestamp=base.start_timestamp,
            end_timestamp=base.end_timestamp,
            bars=base.bars,
            data_hash=base.data_hash,
        )
        for label, base in zip(labels, base_windows, strict=True)
    ]
    ensure_no_overlap(windows)
    return windows


def _find_best_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    directory = latest.parent
    candidates = [*directory.glob("*.parquet"), *directory.glob("*.csv")]
    best_path = latest
    best_rows = -1
    for candidate in candidates:
        try:
            rows = len(load_historical_ohlcv(candidate))
        except Exception:  # noqa: BLE001
            continue
        if rows > best_rows:
            best_rows = rows
            best_path = candidate
    return best_path


def _selected_labels(mode: str) -> set[str]:
    if mode == "dry-run" or mode == "all":
        return {"calibration", "validation_1", "validation_2", "holdout"}
    if mode == "calibration":
        return {"calibration"}
    if mode == "validation":
        return {"validation_1", "validation_2"}
    if mode == "holdout":
        return {"holdout"}
    raise ValueError(mode)


def _run_window_dry(
    *,
    window: EvaluationWindow,
    config: dict[str, Any],
    profile: dict[str, Any],
    data: pd.DataFrame,
    output_dir: Path,
    data_path: Path,
    codex_planned: bool,
) -> dict[str, Any]:
    window_data = data.iloc[window.start_index : window.end_index].reset_index(drop=True)
    source_policies = config.get(
        "source_policies",
        ["state_aware_breakout", "state_aware_momentum"],
    )
    max_candidates = int(
        (config.get("windows") or {}).get(window.label, {}).get(
            "max_candidates", config.get("max_candidates", 20)
        )
    )
    candidates = select_candidate_setups_from_data(
        profile=profile,
        data=window_data,
        source_policies=list(source_policies),
        max_candidates=max_candidates,
        warmup_bars=int(config.get("warmup_bars", 50)),
        min_spacing_bars=int(config.get("min_spacing_bars", 3)),
        data_hash=window.data_hash,
        index_offset=window.start_index,
    )
    result = {
        "version": "V1.9",
        "window_label": window.label,
        "window": window.to_dict(),
        "data_path": str(data_path),
        "candidates_found": len(candidates),
        "candidates": [candidate_to_dict(candidate) for candidate in candidates],
        "baseline_policy_distribution": dict(
            Counter(candidate.baseline_policy for candidate in candidates)
        ),
        "baseline_side_distribution": dict(
            Counter(candidate.baseline_decision for candidate in candidates)
        ),
        "baselines": _baseline_summaries(candidates),
        "gpt_setup_review": {
            "executed": False,
            "submitted": 0,
            "reason": (
                "Codex CLI execution is intentionally skipped in dry-run."
                if not codex_planned
                else (
                    "Window execution is prepared, but this V1.9 runner only performs "
                    "dry selection here."
                )
            ),
            "net_pnl": None,
            "parse_success": None,
            "risk_rejects": None,
        },
        "ledger_pnl_matches_official": None,
        "anti_overfit_role": _window_purpose(config, window.label),
        "holdout_locked": window.label == "holdout",
        "safety": "Aucun appel Codex CLI et aucun ordre reel dans ce dry-run.",
    }
    _write_window_report(output_dir, result)
    return result


def _run_window_codex(
    *,
    window: EvaluationWindow,
    config: dict[str, Any],
    config_path: Path,
    data: pd.DataFrame,
    output_dir: Path,
    data_path: Path,
    cache_options: dict[str, bool],
) -> dict[str, Any]:
    input_dir = output_dir / "_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    window_data_path = input_dir / f"{window.label}_ohlcv.csv"
    data.iloc[window.start_index : window.end_index].to_csv(window_data_path, index=False)
    output_prefix = f"{window.label}_setup_review"
    source_policies = ",".join(
        config.get("source_policies", ["state_aware_breakout", "state_aware_momentum"])
    )
    max_candidates = int(
        (config.get("windows") or {}).get(window.label, {}).get(
            "max_candidates", config.get("max_candidates", 20)
        )
    )
    command = [
        sys.executable,
        "scripts/run_codex_setup_review.py",
        "--profile",
        "4h",
        "--max-candidates",
        str(max_candidates),
        "--source-policies",
        source_policies,
        "--allow-codex-cli",
        "--data-path",
        str(window_data_path),
        "--output-dir",
        str(output_dir),
        "--output-prefix",
        output_prefix,
        "--version",
        str(config.get("version", "V1.9A")),
        "--window-label",
        window.label,
        "--evaluation-run-id",
        output_dir.name,
        "--evaluation-config",
        str(config_path),
    ]
    if cache_options.get("use_decision_cache"):
        command.append("--use-decision-cache")
    if cache_options.get("cache_readonly"):
        command.append("--cache-readonly")
    if cache_options.get("cache_write"):
        command.append("--cache-write")
    if cache_options.get("refresh_cache"):
        command.append("--refresh-cache")
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=max_candidates * 90,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Codex setup review window failed: "
            f"exit={completed.returncode}, stderr={completed.stderr[-2000:]}"
        )
    report_path = output_dir / f"{output_prefix}.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["window_label"] = window.label
    report["window"] = window.to_dict()
    report["data_path"] = str(data_path)
    report["codex_cli_called"] = True
    report["gpt_setup_review"] = {
        "executed": True,
        "submitted": report.get("candidates_submitted", 0),
        "net_pnl": report.get("realized_pnl"),
        "final_equity_pnl": report.get("final_equity_pnl"),
        "parse_success": report.get("final_parse_success_rate"),
        "risk_rejects": report.get("risk_rejects"),
    }
    report["baselines"] = _baseline_summaries(
        [
            CandidateSetup(**review["candidate"])
            for review in report.get("reviews", [])
            if isinstance(review, dict) and isinstance(review.get("candidate"), dict)
        ]
    )
    report["anti_overfit_role"] = _window_purpose(config, window.label)
    report["holdout_locked"] = window.label == "holdout"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (output_dir / f"{output_prefix}.md").write_text(
        _codex_window_markdown(report),
        encoding="utf-8",
    )
    return report


def _baseline_summaries(candidates: list[CandidateSetup]) -> dict[str, Any]:
    policies = [
        "no_trade",
        "state_aware_momentum",
        "state_aware_breakout",
        "llm_offline_conservative",
    ]
    summaries: dict[str, Any] = {}
    for policy in policies:
        if policy in {"no_trade", "llm_offline_conservative"}:
            active = []
        else:
            active = [candidate for candidate in candidates if candidate.baseline_policy == policy]
        summaries[policy] = {
            "execution_mode": "dry_run_signal_count",
            "trade_count": len(active),
            "net_pnl": 0.0 if policy == "no_trade" else None,
            "gross_pnl": 0.0 if policy == "no_trade" else None,
            "fees": 0.0,
            "slippage": 0.0,
            "max_drawdown": 0.0 if policy == "no_trade" else None,
            "risk_rejects": 0,
            "score_prudent": 0.0 if policy == "no_trade" else None,
            "note": (
                "Dry-run: baseline signaux seulement, pas de simulation paper officielle."
                if policy != "no_trade"
                else "Reference sans trade."
            ),
        }
    return summaries


def _window_purpose(config: dict[str, Any], label: str) -> str:
    return str((config.get("windows") or {}).get(label, {}).get("purpose", ""))


def _write_window_report(output_dir: Path, result: dict[str, Any]) -> None:
    json_path = output_dir / f"{result['window_label']}_setup_review.json"
    md_path = output_dir / f"{result['window_label']}_setup_review.md"
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    md_path.write_text(_window_markdown(result), encoding="utf-8")


def _codex_window_markdown(result: dict[str, Any]) -> str:
    window = result.get("window", {})
    return "\n".join(
        [
            f"# Calibration anti-overfit Codex - {result.get('window_label')}",
            "",
            f"- Version : {result.get('version')}",
            f"- Index : {window.get('start_index')} -> {window.get('end_index')}",
            f"- Periode : {window.get('start_timestamp')} -> {window.get('end_timestamp')}",
            f"- Candidats trouves : {result.get('candidates_found')}",
            f"- Candidats soumis : {result.get('candidates_submitted')}",
            f"- JSON valid rate : {result.get('json_valid_rate')}",
            f"- Enum violations : {result.get('enum_violations_count')}",
            f"- Parser fallbacks : {result.get('strict_parser_fallback_count')}",
            f"- Postprocessor fallbacks : {result.get('postprocessor_fallbacks')}",
            f"- Risk rejects : {result.get('risk_rejects')}",
            f"- Decisions : {result.get('decision_distribution')}",
            f"- Decisions brutes : {result.get('raw_decision_distribution')}",
            f"- Overrides contraintes : {result.get('constraint_overrides')}",
            f"- SHORT overrides : {result.get('short_overrides')}",
            f"- Exit policy overrides : {result.get('exit_policy_overrides')}",
            f"- CLOSE delayed count : {result.get('agent_close_delayed_count')}",
            f"- Active decision rate : {result.get('validation_rate')}",
            f"- Ledger trades : {result.get('ledger_trade_count')}",
            f"- Ledger PnL matches official : {result.get('ledger_pnl_matches_official')}",
            (
                "- Positions ouvertes/fermees : "
                f"{result.get('paper_open_position_events')} / {result.get('positions_closed')}"
            ),
            f"- PnL brut : {_gross_pnl(result)}",
            f"- Fees : {result.get('fees')}",
            f"- Slippage : {result.get('slippage')}",
            f"- PnL net : {result.get('realized_pnl')}",
            f"- Unrealized PnL : {result.get('unrealized_pnl')}",
            f"- Final equity PnL : {result.get('final_equity_pnl')}",
            f"- Force closed count : {result.get('force_closed_count')}",
            f"- Setup quality : {result.get('setup_quality_distribution')}",
            f"- Duree moyenne Codex CLI : {result.get('average_duration_seconds')}",
            "",
            "## Baselines meme fenetre",
            json.dumps(result.get("baselines", {}), indent=2, ensure_ascii=False),
            "",
            "## Ledger officiel",
            json.dumps(result.get("closed_trades_ledger", []), indent=2, ensure_ascii=False),
            "",
            "Calibration seulement. Validation et holdout non executes.",
            "Le systeme V1.9A ne peut toujours pas passer d'ordre reel.",
        ]
    )


def _gross_pnl(result: dict[str, Any]) -> float:
    return sum(
        float(trade.get("gross_pnl") or 0.0)
        for trade in result.get("closed_trades_ledger", [])
    )


def _window_markdown(result: dict[str, Any]) -> str:
    window = result["window"]
    return "\n".join(
        [
            f"# Fenetre anti-overfit - {result['window_label']}",
            "",
            f"- Role : {result.get('anti_overfit_role')}",
            f"- Index : {window['start_index']} -> {window['end_index']}",
            f"- Periode : {window['start_timestamp']} -> {window['end_timestamp']}",
            f"- Bougies : {window['bars']}",
            f"- Hash donnees : {window['data_hash']}",
            f"- Candidats trouves : {result['candidates_found']}",
            f"- Distribution policies : {result['baseline_policy_distribution']}",
            f"- Distribution sides : {result['baseline_side_distribution']}",
            f"- GPT execute : {result['gpt_setup_review']['executed']}",
            f"- Ledger PnL matches official : {result['ledger_pnl_matches_official']}",
            "",
            "## Baselines",
            json.dumps(result["baselines"], indent=2, ensure_ascii=False),
            "",
            result["safety"],
        ]
    )
