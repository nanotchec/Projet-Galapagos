"""Script to audit intrabar data lineage."""
from __future__ import annotations

import argparse

from galapagos.research.intrabar.data_lineage import inspect_intrabar_lineage
from galapagos.research.report_models import write_research_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intrabar", required=True, help="Path to intrabar parquet file")
    parser.add_argument("--version", default="v1.20.1")
    args = parser.parse_args()

    result = inspect_intrabar_lineage(args.intrabar, version=args.version)
    
    # Save JSON
    v_v = args.version.replace(".", "_")
    report_name = f"intrabar_data_lineage_{v_v}"
    
    write_research_report(
        name=report_name,
        payload=result,
        title=f"Intrabar Data Lineage Audit - {args.version}",
        lines=[
            f"- **File**: `{result.get('intrabar_file_path')}`",
            f"- **Status**: `{result.get('lineage_status')}`",
            f"- **Rows**: {result.get('rows')}",
            f"- **Range**: {result.get('first_timestamp')} to {result.get('last_timestamp')}",
            f"- **Days**: {result.get('inferred_days')}",
            f"- **Manifest**: {result.get('manifest_exists')}",
        ],
        output_dir="reports/research"
    )
    
    print(f"Lineage report generated: reports/research/{report_name}.json")

if __name__ == "__main__":
    main()
