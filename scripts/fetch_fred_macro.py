from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.macro.fred_client import fred_env_status
from galapagos.data.macro.fred_collector import collect_fred_series
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", default="DFF,DGS2,DGS10,T10Y2Y,VIXCLS,SP500,NASDAQCOM")
    parser.add_argument("--start", default="2019-01-01")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    series_ids = [item.strip() for item in args.series.split(",") if item.strip()]
    if args.dry_run or fred_env_status()["FRED_API_KEY"] != "configured":
        payload = {
            "version": "V1.12.2",
            "dry_run": args.dry_run,
            "fred_api_key": fred_env_status()["FRED_API_KEY"],
            "status": (
                "requires_api_key"
                if fred_env_status()["FRED_API_KEY"] != "configured"
                else "planned"
            ),
            "network_called": False,
            "series": series_ids,
        }
    else:
        collected = collect_fred_series(series_ids, args.start)
        output = Path("data/silver/macro/fred")
        output.mkdir(parents=True, exist_ok=True)
        available_series = []
        unavailable_series = []
        total_rows = 0
        start_timestamps = []
        end_timestamps = []
        for series_id, value in collected.items():
            frame = value["data"]
            if not frame.empty:
                frame.to_csv(output / f"{series_id}.csv", index=False)
                available_series.append(series_id)
                total_rows += len(frame)
                start_timestamps.append(str(frame["timestamp"].min()))
                end_timestamps.append(str(frame["timestamp"].max()))
            else:
                unavailable_series.append(series_id)
        payload = {
            "version": "V1.12.2",
            "dry_run": False,
            "fred_api_key": "configured",
            "network_called": True,
            "output_dir": str(output),
            "available_series": available_series,
            "unavailable_series": unavailable_series,
            "rows": total_rows,
            "start_timestamp": min(start_timestamps) if start_timestamps else None,
            "end_timestamp": max(end_timestamps) if end_timestamps else None,
            "series_status": {
                key: {"status": value["status"], "rows": value["rows"]}
                for key, value in collected.items()
            },
        }
    write_research_report(
        name="fred_macro_readiness_v1_12_2",
        payload=payload,
        title="FRED Macro Readiness V1.12.2",
        lines=[
            f"FRED_API_KEY: {payload['fred_api_key']}.",
            f"Status: {payload.get('status', 'fetched')}.",
            f"Series disponibles: {payload.get('available_series', [])}.",
            f"Series indisponibles: {payload.get('unavailable_series', [])}.",
            "Aucun secret affiche.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
