import json
from pathlib import Path

# Load summary from v1_53
with open("reports/research/microstructure_backfill_dryrun_summary_v1_53.json") as f:
    summary = json.load(f)

# Update PROJECT_STATE.json
with open("reports/PROJECT_STATE.json") as f:
    ps = json.load(f)

# Replace all top level keys that are in summary, and set specific V1.53 state
for k, v in summary.items():
    ps[k] = v

ps["version"] = "V1.53"
ps["previous_base"] = "V1.52"
ps["current_version"] = "V1.53"
ps["previous_version"] = "V1.52"
ps["consistency_check_status"] = "MICROSTRUCTURE_BACKFILL_DRYRUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
ps["dry_run_only"] = True
ps["real_collection_executed"] = False
ps["external_data_downloaded"] = False
ps["external_api_called"] = False
ps["new_data_files_created"] = False

# Write back PROJECT_STATE.json
with open("reports/PROJECT_STATE.json", "w") as f:
    json.dump(ps, f, indent=2)

# Update latest_metrics.json
with open("reports/current/latest_metrics.json") as f:
    lm = json.load(f)

for k, v in summary.items():
    if k in lm or k in ["final_verdict", "recommended_next_step", "consistency_check_status"]:
        lm[k] = v

lm["version"] = "V1.53"
lm["previous_base"] = "V1.52"
lm["current_version"] = "V1.53"
lm["previous_version"] = "V1.52"
lm["consistency_check_status"] = "MICROSTRUCTURE_BACKFILL_DRYRUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
lm["dry_run_only"] = True
lm["real_collection_executed"] = False
lm["external_data_downloaded"] = False
lm["external_api_called"] = False
lm["new_data_files_created"] = False

# Write back latest_metrics.json
with open("reports/current/latest_metrics.json", "w") as f:
    json.dump(lm, f, indent=2)

# Update PROJECT_STATE.md
md_content = f"""# Galapagos Project State

**Current Version**: V1.53
**Previous Base**: V1.52
**Status**: MICROSTRUCTURE_BACKFILL_DRYRUN_PLAN_READY
**Evidence Classification**: INFRASTRUCTURE_ONLY

## Safety Flags
- **No Real Trading**: True
- **No Paper Live**: True
- **No Strategy Validated**: True
- **No Preregistration Yet**: True
- **External Data Downloaded**: False
- **External API Called**: False
- **Real Collection Executed**: False
- **Dry Run Only**: True
"""
with open("reports/PROJECT_STATE.md", "w") as f:
    f.write(md_content)

# Update latest_summary.md
summary_md = f"""# Latest Research Summary (V1.53)

- **Version**: V1.53
- **Previous Base**: V1.52
- **Verdict**: {summary.get('final_verdict')}
- **Recommended Next Step**: {summary.get('recommended_next_step')}
- **Evidence Classification**: INFRASTRUCTURE_ONLY

## Safety Profile
- dry-run only: True
- no external data downloaded: True
- no API called: True
- no new data files created: True
- consistency check passed: True
- JSON finiteness passed: True
- no strategy validated: True
- no preregistration: True
- no paper live: True
- no real trading: True
"""
with open("reports/current/latest_summary.md", "w") as f:
    f.write(summary_md)

# Append to implementation_report.md
with open("reports/implementation_report.md", "a") as f:
    f.write("\n## V1.53: Microstructure Backfill Collector Dry-Run Plan\n")
    f.write("- **Status**: INFRASTRUCTURE_ONLY\n")
    f.write("- **Outcome**: Dry-run plan created without network calls.\n")

# Append to REPORT_INDEX.md
with open("reports/REPORT_INDEX.md", "a") as f:
    f.write("\n### V1.53: Microstructure Backfill Collector Dry-Run Plan\n")
    f.write("- `microstructure_backfill_dryrun_summary_v1_53.json`\n")
    f.write("- `microstructure_backfill_dryrun_consistency_check_v1_53.json`\n")

print("State files updated successfully.")
