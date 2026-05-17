from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.variant_comparison import (
    summarize_variant_windows,
    summarize_window_report,
)
from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--cache-readonly", action="store_true")
    args = parser.parse_args()
    payload = replay_cached_variants(
        config_path=Path(args.config),
        cache_readonly=args.cache_readonly,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def replay_cached_variants(*, config_path: Path, cache_readonly: bool) -> dict:
    if not cache_readonly:
        raise RuntimeError("V1.10.6 requires --cache-readonly.")
    config = load_yaml(config_path)
    windows = list((config.get("windows") or {}).keys())
    if "holdout" in windows or config.get("holdout_enabled") is not False:
        raise RuntimeError("Holdout is blocked in V1.10.6 cached variant replay.")
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
    run_id = (
        f"cached_variants_v1_10_6_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_"
        f"{str(uuid4())[:8]}"
    )
    output_dir = Path("reports/evaluation") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "_inputs"
    input_dir.mkdir(exist_ok=True)

    source_maps = {}
    cache_source_results = {}
    for label in windows:
        window = base_windows[label]
        window_csv = input_dir / f"{label}_ohlcv.csv"
        data.iloc[window.start_index : window.end_index].to_csv(window_csv, index=False)
        source_report = _run_setup_review(
            config_path=Path(config["base_cache_config"]),
            data_path=window_csv,
            output_dir=output_dir,
            output_prefix=f"{label}_cache_source",
            label=label,
            run_id=run_id,
            source_policies=config.get("source_policies", []),
            max_candidates=_max_candidates(config, label),
            extra_args=["--use-decision-cache", "--cache-readonly"],
        )
        cache = source_report.get("decision_cache") or {}
        if int(cache.get("hits") or 0) != int(source_report.get("candidates_submitted") or 0):
            raise RuntimeError(f"Cache miss detected in source replay for {label}: {cache}")
        source_maps[label] = _write_decision_map(output_dir, label, source_report)
        cache_source_results[label] = {
            "cache_hits": cache.get("hits", 0),
            "cache_misses": cache.get("misses", 0),
            "submitted": source_report.get("candidates_submitted", 0),
        }

    variant_results: dict[str, list[dict]] = {}
    raw_reports: dict[str, dict[str, dict]] = {}
    for variant_name, variant_config in (config.get("variants") or {}).items():
        variant_results[variant_name] = []
        raw_reports[variant_name] = {}
        for label in windows:
            with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
                _write_variant_config(handle, config, variant_name, variant_config)
                variant_config_path = Path(handle.name)
            try:
                report = _run_setup_review(
                    config_path=variant_config_path,
                    data_path=input_dir / f"{label}_ohlcv.csv",
                    output_dir=output_dir,
                    output_prefix=f"{variant_name}_{label}",
                    label=label,
                    run_id=run_id,
                    source_policies=config.get("source_policies", []),
                    max_candidates=_max_candidates(config, label),
                    extra_args=["--cached-decisions-json", str(source_maps[label])],
                )
            finally:
                variant_config_path.unlink(missing_ok=True)
            summary = summarize_window_report(report)
            variant_results[variant_name].append(summary)
            raw_reports[variant_name][label] = report

    comparison = summarize_variant_windows(variant_results)
    payload = {
        "version": "V1.10.6",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "config_path": str(config_path),
        "evaluation_run_id": run_id,
        "windows": windows,
        "holdout_used": False,
        "cache_source": cache_source_results,
        "cache_hits": sum(int(item["cache_hits"]) for item in cache_source_results.values()),
        "codex_calls": 0,
        "variant_results": variant_results,
        "comparison": comparison,
        "answers": _answers(comparison),
        "safety": "Le système V1.10.6 ne peut toujours pas passer d’ordre réel.",
    }
    _write_report(output_dir, payload)
    return payload


def _run_setup_review(
    *,
    config_path: Path,
    data_path: Path,
    output_dir: Path,
    output_prefix: str,
    label: str,
    run_id: str,
    source_policies: list[str],
    max_candidates: int,
    extra_args: list[str],
) -> dict:
    command = [
        sys.executable,
        "scripts/run_codex_setup_review.py",
        "--profile",
        "4h",
        "--max-candidates",
        str(max_candidates),
        "--source-policies",
        ",".join(source_policies),
        "--data-path",
        str(data_path),
        "--output-dir",
        str(output_dir),
        "--output-prefix",
        output_prefix,
        "--version",
        "V1.10.6",
        "--window-label",
        label,
        "--evaluation-run-id",
        run_id,
        "--evaluation-config",
        str(config_path),
        *extra_args,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=max_candidates * 20,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Cached setup review failed for {output_prefix}: {completed.stderr[-2000:]}"
        )
    return json.loads((output_dir / f"{output_prefix}.json").read_text(encoding="utf-8"))


def _write_decision_map(output_dir: Path, label: str, report: dict) -> Path:
    payload = {
        review["candidate"]["candidate_id"]: review["raw_response"]
        for review in report.get("reviews", [])
    }
    path = output_dir / f"{label}_cached_decisions_map.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_variant_config(
    handle,
    base_config: dict,
    variant_name: str,
    variant_config: dict,
) -> None:
    payload = {
        "version": "V1.10.6",
        "evaluation_name": variant_name,
        "profile": base_config.get("profile"),
        "asset": base_config.get("asset"),
        "timeframe": base_config.get("timeframe"),
        "source_policies": base_config.get("source_policies"),
        "min_bars_per_window": base_config.get("min_bars_per_window"),
        "warmup_bars": base_config.get("warmup_bars"),
        "min_spacing_bars": base_config.get("min_spacing_bars"),
        **variant_config,
    }
    import yaml

    yaml.safe_dump(payload, handle, sort_keys=False)


def _find_longest_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    candidates = [*latest.parent.glob("*.parquet"), *latest.parent.glob("*.csv")]
    return max(candidates, key=lambda path: len(load_historical_ohlcv(path)))


def _max_candidates(config: dict, label: str) -> int:
    return int((config.get("windows") or {}).get(label, {}).get("max_candidates", 20))


def _answers(comparison: dict) -> dict:
    best = comparison.get("best_total_pnl") or {}
    stable = comparison.get("most_stable") or {}
    lowest = comparison.get("lowest_costs") or {}
    return {
        "best_total_pnl": best.get("variant"),
        "most_stable": stable.get("variant"),
        "lowest_costs": lowest.get("variant"),
        "holdout_locked": True,
        "verdicts": comparison.get("verdicts", []),
    }


def _write_report(output_dir: Path, payload: dict) -> None:
    json_path = output_dir / "cached_variants_v1_10_6.json"
    md_path = output_dir / "cached_variants_v1_10_6.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(payload), encoding="utf-8")
    root_json = Path("reports/evaluation/cached_variants_v1_10_6.json")
    root_md = Path("reports/evaluation/cached_variants_v1_10_6.md")
    root_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    root_md.write_text(_markdown(payload), encoding="utf-8")


def _markdown(payload: dict) -> str:
    rows = payload.get("comparison", {}).get("rows", [])
    lines = [
        "# Cached variants V1.10.6",
        "",
        f"- Cache hits source : {payload.get('cache_hits')}",
        f"- Appels Codex CLI : {payload.get('codex_calls')}",
        f"- Holdout utilise : {payload.get('holdout_used')}",
        f"- Verdicts : {payload.get('comparison', {}).get('verdicts')}",
        "",
        "| Variante | Total PnL | Mean window | Min window | PnL std | Trades | Costs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {variant} | {total_net_pnl:.2f} | {mean_window_pnl:.2f} | "
            "{min_window_pnl:.2f} | {pnl_std:.2f} | {total_trades} | {total_costs:.2f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Details",
            json.dumps(payload.get("variant_results"), indent=2, ensure_ascii=False),
            "",
            payload["safety"],
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
