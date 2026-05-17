from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.macro.fred_client import fred_env_status
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    env = fred_env_status()
    payload = {
        "version": "V1.12.2",
        "fred_api_key": env["FRED_API_KEY"],
        "status": (
            "available_for_fetch" if env["FRED_API_KEY"] == "configured" else "requires_api_key"
        ),
        "secret_logged": False,
        "series": ["DFF", "DGS2", "DGS10", "T10Y2Y", "VIXCLS", "SP500", "NASDAQCOM"],
    }
    write_research_report(
        name="fred_macro_readiness_v1_12_2",
        payload=payload,
        title="FRED Macro Readiness V1.12.2",
        lines=[
            f"FRED_API_KEY: {payload['fred_api_key']}.",
            f"Status: {payload['status']}.",
            "La cle n'est jamais affichee.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
