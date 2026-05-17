from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--windows", default="calibration,validation_1,validation_2")
    parser.add_argument("--use-decision-cache", action="store_true")
    parser.add_argument("--cache-readonly", action="store_true")
    parser.add_argument("--allow-holdout", action="store_true")
    args = parser.parse_args()
    payload = replay_cached_decisions(
        config_path=Path(args.config),
        windows=[item.strip() for item in args.windows.split(",") if item.strip()],
        use_decision_cache=args.use_decision_cache,
        cache_readonly=args.cache_readonly,
        allow_holdout=args.allow_holdout,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def replay_cached_decisions(
    *,
    config_path: Path,
    windows: list[str],
    use_decision_cache: bool,
    cache_readonly: bool,
    allow_holdout: bool,
) -> dict:
    if not use_decision_cache or not cache_readonly:
        raise RuntimeError("Cached replay requires --use-decision-cache --cache-readonly.")
    if "holdout" in windows and not allow_holdout:
        raise RuntimeError("Holdout cached replay is blocked by default.")
    config = load_yaml(config_path)
    profile = load_profile(str(config.get("profile", "galapagos_4h")))
    data_path = _find_longest_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found.")
    data = load_historical_ohlcv(data_path).sort_values("timestamp").drop_duplicates("timestamp")
    labels = ["calibration", "validation_1", "validation_2", "holdout"]
    base_windows = dict(
        zip(
            labels,
            split_ohlcv_into_windows(data, 4, int(config.get("min_bars_per_window", 80))),
            strict=True,
        )
    )
    output_dir = Path("reports/evaluation") / (
        f"cached_replay_v1_10_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_"
        f"{str(uuid4())[:8]}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "_inputs"
    input_dir.mkdir(exist_ok=True)
    evaluation_run_id = "decision_cache_v1_10_5"
    results = []
    for label in windows:
        window = base_windows[label]
        window_csv = input_dir / f"{label}_ohlcv.csv"
        data.iloc[window.start_index : window.end_index].to_csv(window_csv, index=False)
        output_prefix = f"{label}_cached_replay_setup_review"
        command = [
            sys.executable,
            "scripts/run_codex_setup_review.py",
            "--profile",
            "4h",
            "--max-candidates",
            str(_max_candidates(config, label)),
            "--source-policies",
            ",".join(config.get("source_policies", [])),
            "--data-path",
            str(window_csv),
            "--output-dir",
            str(output_dir),
            "--output-prefix",
            output_prefix,
            "--version",
            "V1.10.5-cached-replay",
            "--window-label",
            label,
            "--evaluation-run-id",
            evaluation_run_id,
            "--evaluation-config",
            str(config_path),
            "--use-decision-cache",
            "--cache-readonly",
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_max_candidates(config, label) * 10,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Cached replay window failed: "
                f"{label}, exit={completed.returncode}, stderr={completed.stderr[-2000:]}"
            )
        report = json.loads((output_dir / f"{output_prefix}.json").read_text())
        results.append(_window_summary(label, report))
    payload = {
        "version": "V1.10.5",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "config_path": str(config_path),
        "windows": windows,
        "holdout_used": "holdout" in windows,
        "window_results": results,
        "result_hash": _result_hash(results),
        "total_cache_hits": sum(
            int((item.get("decision_cache") or {}).get("hits") or 0) for item in results
        ),
        "total_readonly_misses": sum(
            int((item.get("decision_cache") or {}).get("readonly_misses") or 0)
            for item in results
        ),
        "safety": "Le système V1.10.5 ne peut toujours pas passer d’ordre réel.",
    }
    _write_report(output_dir, payload)
    return payload


def _window_summary(label: str, report: dict) -> dict:
    return {
        "window": label,
        "candidates_submitted": report.get("candidates_submitted"),
        "decision_distribution": report.get("decision_distribution"),
        "realized_pnl": report.get("realized_pnl"),
        "final_equity_pnl": report.get("final_equity_pnl"),
        "fees": report.get("fees"),
        "slippage": report.get("slippage"),
        "ledger_trade_count": report.get("ledger_trade_count"),
        "ledger_pnl_matches_official": report.get("ledger_pnl_matches_official"),
        "decision_cache": report.get("decision_cache"),
        "risk_rejects": report.get("risk_rejects"),
    }


def _result_hash(results: list[dict]) -> str:
    encoded = json.dumps(results, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _find_longest_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    candidates = [*latest.parent.glob("*.parquet"), *latest.parent.glob("*.csv")]
    return max(candidates, key=lambda path: len(load_historical_ohlcv(path)))


def _max_candidates(config: dict, label: str) -> int:
    return int((config.get("windows") or {}).get(label, {}).get("max_candidates", 20))


def _write_report(output_dir: Path, payload: dict) -> None:
    json_path = output_dir / "cached_replay_v1_10_5.json"
    md_path = output_dir / "cached_replay_v1_10_5.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Cached replay V1.10.5",
        "",
        f"- Fenetres : {payload['windows']}",
        f"- Holdout utilise : {payload['holdout_used']}",
        f"- Cache hits : {payload['total_cache_hits']}",
        f"- Cache readonly misses : {payload['total_readonly_misses']}",
        f"- Result hash : {payload['result_hash']}",
        "",
        json.dumps(payload["window_results"], indent=2, ensure_ascii=False),
        "",
        payload["safety"],
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
