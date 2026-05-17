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

from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--windows", default="calibration,validation_1,validation_2")
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--max-calls", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--allow-holdout", action="store_true")
    args = parser.parse_args()
    payload = build_decision_cache(
        config_path=Path(args.config),
        windows=[item.strip() for item in args.windows.split(",") if item.strip()],
        allow_codex_cli=args.allow_codex_cli,
        max_calls=args.max_calls,
        dry_run=args.dry_run,
        refresh_cache=args.refresh_cache,
        allow_holdout=args.allow_holdout,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def build_decision_cache(
    *,
    config_path: Path,
    windows: list[str],
    allow_codex_cli: bool,
    max_calls: int,
    dry_run: bool,
    refresh_cache: bool,
    allow_holdout: bool,
) -> dict:
    if "holdout" in windows and not allow_holdout:
        raise RuntimeError("Holdout cache build is blocked by default.")
    if not dry_run and not allow_codex_cli:
        raise RuntimeError("Decision cache build requires --allow-codex-cli unless --dry-run.")
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
    planned_calls = sum(_max_candidates(config, label) for label in windows)
    if planned_calls > max_calls:
        raise RuntimeError(f"Planned calls {planned_calls} exceeds --max-calls {max_calls}.")

    evaluation_run_id = "decision_cache_v1_10_5"
    output_dir = Path("reports/evaluation") / (
        f"decision_cache_build_v1_10_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_"
        f"{str(uuid4())[:8]}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "_inputs"
    input_dir.mkdir(exist_ok=True)
    results = []
    for label in windows:
        window = base_windows[label]
        window_csv = input_dir / f"{label}_ohlcv.csv"
        data.iloc[window.start_index : window.end_index].to_csv(window_csv, index=False)
        if dry_run:
            results.append({"window": label, "planned_calls": _max_candidates(config, label)})
            continue
        output_prefix = f"{label}_cache_build_setup_review"
        command = [
            sys.executable,
            "scripts/run_codex_setup_review.py",
            "--profile",
            "4h",
            "--max-candidates",
            str(_max_candidates(config, label)),
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
            "V1.10.5-cache-build",
            "--window-label",
            label,
            "--evaluation-run-id",
            evaluation_run_id,
            "--evaluation-config",
            str(config_path),
            "--use-decision-cache",
            "--cache-write",
        ]
        if refresh_cache:
            command.append("--refresh-cache")
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_max_candidates(config, label) * 90,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Cache build window failed: "
                f"{label}, exit={completed.returncode}, stderr={completed.stderr[-2000:]}"
            )
        report = json.loads((output_dir / f"{output_prefix}.json").read_text())
        results.append(
            {
                "window": label,
                "requested_decisions": report.get("candidates_submitted", 0),
                "cache": report.get("decision_cache", {}),
                "parse_success": report.get("final_parse_success_rate"),
                "codex_calls": report.get("decision_cache", {}).get("written", 0),
                "failures": report.get("strict_parser_fallback_count", 0),
            }
        )
    payload = {
        "version": "V1.10.5",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "config_path": str(config_path),
        "windows": windows,
        "dry_run": dry_run,
        "holdout_used": "holdout" in windows,
        "requested_decisions": planned_calls,
        "cache_hits": sum(int((item.get("cache") or {}).get("hits") or 0) for item in results),
        "cache_misses": sum(
            int((item.get("cache") or {}).get("misses") or 0)
            + int((item.get("cache") or {}).get("written") or 0)
            for item in results
        ),
        "codex_calls": sum(int(item.get("codex_calls") or 0) for item in results),
        "cache_entries_written": sum(
            int((item.get("cache") or {}).get("written") or 0) for item in results
        ),
        "windows_results": results,
        "safety": "Le système V1.10.5 ne peut toujours pas passer d’ordre réel.",
    }
    _write_report(output_dir, payload)
    return payload


def _find_longest_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    candidates = [*latest.parent.glob("*.parquet"), *latest.parent.glob("*.csv")]
    return max(candidates, key=lambda path: len(load_historical_ohlcv(path)))


def _max_candidates(config: dict, label: str) -> int:
    return int((config.get("windows") or {}).get(label, {}).get("max_candidates", 20))


def _write_report(output_dir: Path, payload: dict) -> None:
    json_path = output_dir / "decision_cache_build_v1_10_5.json"
    md_path = output_dir / "decision_cache_build_v1_10_5.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Decision cache build V1.10.5",
        "",
        f"- Decisions demandees : {payload['requested_decisions']}",
        f"- Cache hits : {payload['cache_hits']}",
        f"- Cache misses : {payload['cache_misses']}",
        f"- Appels Codex CLI : {payload['codex_calls']}",
        f"- Entrees ecrites : {payload['cache_entries_written']}",
        f"- Holdout utilise : {payload['holdout_used']}",
        "",
        json.dumps(payload["windows_results"], indent=2, ensure_ascii=False),
        "",
        payload["safety"],
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
