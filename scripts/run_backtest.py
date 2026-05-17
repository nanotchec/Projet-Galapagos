from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.backtest_comparison import compare_backtest_profiles
from galapagos.backtest.historical_data import cache_kraken_ohlcv, find_latest_cached_ohlcv
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.reports.backtest_report import generate_backtest_report
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--profile", choices=["30m", "4h", "galapagos_30m", "galapagos_4h"])
    parser.add_argument("--policy", default="simple_momentum")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if args.config:
        config = load_yaml(args.config)
        profiles = config.get("profiles", ["30m", "4h"])
        policy = config.get("mock_decision_policy", "simple_momentum")
        reports_dir = project_path(config.get("output_reports_dir", "reports/backtests"))
        capital = float(config.get("initial_capital_per_profile", 10_000))
        force_close_at_end = bool(config.get("force_close_at_end", False))
    else:
        config = {"ad_hoc": True}
        profiles = [args.profile or "30m"]
        policy = args.policy
        reports_dir = project_path("reports/backtests")
        capital = 10_000.0
        force_close_at_end = False

    run_id = str(uuid4())
    profile_results = {}
    data_hashes = {}
    metadata = {}
    for profile_name in profiles:
        profile = load_profile(profile_name)
        data_path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
        if data_path is None:
            data_path = cache_kraken_ohlcv(
                symbol=profile["symbol"],
                timeframe=profile["timeframe"],
                days=args.days,
            ).data_path
        result = ReplayEngine(
            profile=profile,
            data_path=data_path,
            risk_config=load_yaml("configs/risk.yaml"),
            initial_capital=capital,
            policy=policy,
            force_close_at_end=force_close_at_end,
        ).run()
        profile_results[profile["name"]] = result
        data_hashes[profile["name"]] = _file_hash(data_path)
        metadata[profile["name"]] = _load_metadata(data_path)

    report_payload = {
        "run_id": run_id,
        "config": config,
        "period": {profile: result["period"] for profile, result in profile_results.items()},
        "data_source": "kraken historical cache",
        "data_hashes": data_hashes,
        "metadata": metadata,
        "profiles": list(profile_results),
        "policy": policy,
        "force_close_at_end": force_close_at_end,
        "metrics": {profile: result["metrics"] for profile, result in profile_results.items()},
        "comparison": compare_backtest_profiles(
            {profile: result["metrics"] for profile, result in profile_results.items()}
        ),
        "anti_leakage": {
            profile: result.get("anti_leakage", {}) for profile, result in profile_results.items()
        },
        "time_convention": {
            profile: result.get("time_convention", {})
            for profile, result in profile_results.items()
        },
        "raw_results": profile_results,
    }
    paths = generate_backtest_report(report_payload, reports_dir)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "metrics": report_payload["metrics"],
                "paths": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def _file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_metadata(data_path: str | Path) -> dict:
    path = Path(data_path)
    metadata_files = sorted(path.parent.glob("metadata_*.json"))
    if not metadata_files:
        return {"data_path": str(path), "metadata_status": "missing"}
    for candidate in reversed(metadata_files):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("data_path") == str(path):
            return data
    return json.loads(metadata_files[-1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
