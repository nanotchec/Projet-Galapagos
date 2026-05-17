from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.decision_stability import analyze_decision_stability
from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--repetitions", type=int, default=None)
    parser.add_argument("--windows", default=None)
    parser.add_argument("--max-calls", type=int, default=60)
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run_stability_analysis(
        config_path=args.config,
        repetitions=args.repetitions,
        windows=args.windows,
        max_calls=args.max_calls,
        allow_codex_cli=args.allow_codex_cli,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def run_stability_analysis(
    *,
    config_path: str | Path,
    repetitions: int | None,
    windows: str | None,
    max_calls: int,
    allow_codex_cli: bool,
    dry_run: bool = False,
) -> dict:
    config = load_yaml(config_path)
    profile = load_profile(str(config.get("profile", "galapagos_4h")))
    if profile.get("timeframe") != "4h":
        raise RuntimeError("Codex stability analysis is limited to 4h.")
    selected_windows = _selected_windows(config, windows)
    if "holdout" in selected_windows:
        raise RuntimeError("Holdout is not allowed in V1.10.4 stability analysis.")
    reps = repetitions or int((config.get("evaluation") or {}).get("stability_repetitions", 3))
    planned_calls = reps * _max_candidates(config, selected_windows)
    if not dry_run and planned_calls > max_calls:
        raise RuntimeError(f"Planned calls {planned_calls} exceeds --max-calls {max_calls}.")
    if not dry_run and not allow_codex_cli:
        raise RuntimeError("Real stability analysis requires --allow-codex-cli.")

    evaluation_run_id = (
        f"{config.get('evaluation_name', 'codex_stability')}_"
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{str(uuid4())[:8]}"
    )

    if dry_run:
        data_path = _find_longest_cached_ohlcv(profile["symbol"], profile["timeframe"])
        payload = {
            "version": "V1.10.4",
            "evaluation_run_id": evaluation_run_id,
            "dry_run": True,
            "windows": selected_windows,
            "repetitions": reps,
            "planned_calls": planned_calls,
            "holdout_executed": False,
            "data_required_for_real_run": True,
            "data_available": data_path is not None,
            "status": "dry_run_completed",
        }
        output_dir = Path("reports/evaluation") / evaluation_run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_report(output_dir, payload)
        return payload

    data_path = _find_longest_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found. Required for non-dry-run execution.")
    data = load_historical_ohlcv(data_path).sort_values("timestamp").drop_duplicates("timestamp")
    base_windows = split_ohlcv_into_windows(data, 4, int(config.get("min_bars_per_window", 80)))
    labels = ["calibration", "validation_1", "validation_2", "holdout"]
    windows_by_label = dict(zip(labels, base_windows, strict=True))
    output_dir = Path("reports/evaluation") / evaluation_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "_inputs"
    input_dir.mkdir(exist_ok=True)

    repetitions_payload = []
    calls = 0
    for rep in range(1, reps + 1):
        rep_payload = {"index": rep, "windows": {}}
        for label in selected_windows:
            window = windows_by_label[label]
            max_candidates = int(
                (config.get("windows") or {}).get(label, {}).get(
                    "max_candidates", config.get("max_candidates", 20)
                )
            )
            calls += max_candidates
            window_csv = input_dir / f"{label}_rep{rep}_ohlcv.csv"
            data.iloc[window.start_index : window.end_index].to_csv(window_csv, index=False)
            output_prefix = f"{label}_rep{rep}_setup_review"
            command = [
                sys.executable,
                "scripts/run_codex_setup_review.py",
                "--profile",
                "4h",
                "--max-candidates",
                str(max_candidates),
                "--source-policies",
                ",".join(config.get("source_policies", [])),
                "--allow-codex-cli",
                "--data-path",
                str(window_csv),
                "--output-dir",
                str(output_dir),
                "--output-prefix",
                output_prefix,
                "--version",
                str(config.get("version", "V1.10.4")),
                "--window-label",
                label,
                "--evaluation-run-id",
                evaluation_run_id,
                "--evaluation-config",
                str(config_path),
            ]
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=max_candidates * 90,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "Codex stability window failed: "
                    f"rep={rep}, window={label}, stderr={completed.stderr[-2000:]}"
                )
            report = json.loads((output_dir / f"{output_prefix}.json").read_text())
            report["stability_repetition"] = rep
            report["window"] = window.to_dict()
            (output_dir / f"{output_prefix}.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            rep_payload["windows"][label] = report
        repetitions_payload.append(rep_payload)
    stability = analyze_decision_stability(repetitions_payload)
    payload = {
        "version": "V1.10.4",
        "evaluation_run_id": evaluation_run_id,
        "config_path": str(config_path),
        "data_path": str(data_path),
        "windows_executed": selected_windows,
        "repetitions": reps,
        "codex_cli_calls": calls,
        "holdout_executed": False,
        "repetition_results": repetitions_payload,
        "stability": stability,
        "answers": _answers(stability),
        "safety": "Le système V1.10.4 ne peut toujours pas passer d’ordre réel.",
    }
    _write_report(output_dir, payload)
    return payload


def _selected_windows(config: dict, windows: str | None) -> list[str]:
    if windows:
        selected = [item.strip() for item in windows.split(",") if item.strip()]
    else:
        selected = list((config.get("evaluation") or {}).get("windows") or ["calibration"])
    return selected


def _max_candidates(config: dict, windows: list[str]) -> int:
    return sum(
        int((config.get("windows") or {}).get(window, {}).get("max_candidates", 20))
        for window in windows
    )


def _find_longest_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    candidates = [*latest.parent.glob("*.parquet"), *latest.parent.glob("*.csv")]
    best = latest
    rows = -1
    for candidate in candidates:
        try:
            count = len(load_historical_ohlcv(candidate))
        except Exception:  # noqa: BLE001
            continue
        if count > rows:
            rows = count
            best = candidate
    return best


def _answers(stability: dict) -> dict:
    global_metrics = stability.get("global", {})
    verdict = stability.get("verdict")
    return {
        "same_decisions": (
            "Non, pas suffisamment."
            if verdict in {"MODERATELY_UNSTABLE", "HIGHLY_UNSTABLE"}
            else "Oui, sur ce run limite."
        ),
        "v1101_vs_v1103_noise_possible": "Oui, si le verdict n'est pas STABLE.",
        "compare_independent_variants": (
            "Non recommande sans cache ou consensus."
            if verdict != "STABLE"
            else "Possible, avec prudence."
        ),
        "cache_or_consensus": "Recommander cache decisionnel pour variantes deterministes.",
        "agreement_rate": global_metrics.get("exact_decision_match_rate"),
    }


def _write_report(output_dir: Path, payload: dict) -> None:
    json_path = output_dir / "codex_stability_v1_10_4.json"
    md_path = output_dir / "codex_stability_v1_10_4.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    md_path.write_text(_markdown(payload), encoding="utf-8")


def _markdown(payload: dict) -> str:
    stability = payload.get("stability", {})
    global_metrics = stability.get("global", {})
    lines = [
        "# Stabilite decisionnelle Codex Galapagos V1.10.4",
        "",
        f"- Run id : {payload.get('evaluation_run_id')}",
        f"- Fenetres : {payload.get('windows_executed')}",
        f"- Repetitions : {payload.get('repetitions')}",
        f"- Appels Codex CLI : {payload.get('codex_cli_calls')}",
        f"- Holdout execute : {payload.get('holdout_executed')}",
        f"- Verdict : {stability.get('verdict')}",
        f"- Exact decision match rate global : {global_metrics.get('exact_decision_match_rate')}",
        f"- Flips LONG/NO_TRADE : {global_metrics.get('long_no_trade_flip_count')}",
        "",
        "## Par fenetre",
    ]
    for label, metrics in (stability.get("windows") or {}).items():
        lines.extend(
            [
                f"### {label}",
                f"- Exact match : {metrics.get('exact_decision_match_rate')}",
                f"- Agreement moyen : {metrics.get('decision_agreement_rate_mean')}",
                f"- Flips LONG/NO_TRADE : {metrics.get('long_no_trade_flip_count')}",
                f"- PnL repetitions : {metrics.get('pnl_by_repetition')}",
                f"- PnL variance : {metrics.get('pnl_variance')}",
                f"- Trades repetitions : {metrics.get('trade_count_by_repetition')}",
                f"- Decision distributions : {metrics.get('decision_distribution_by_repetition')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Exemples instables",
            json.dumps(global_metrics.get("unstable_examples", []), indent=2, ensure_ascii=False),
            "",
            "## Reponses",
            json.dumps(payload.get("answers", {}), indent=2, ensure_ascii=False),
            "",
            "## Recommandation",
            "Utiliser un cache decisionnel ou un consensus avant de comparer des variantes "
            "deterministes sur des runs GPT independants.",
            "",
            payload.get("safety", ""),
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
