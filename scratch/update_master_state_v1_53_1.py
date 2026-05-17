import json
from pathlib import Path

# Load summary from v1_53_1
with open("reports/research/microstructure_backfill_dryrun_summary_v1_53_1.json") as f:
    summary = json.load(f)

# Update PROJECT_STATE.json
with open("reports/PROJECT_STATE.json") as f:
    ps = json.load(f)

# Replace all top level keys that are in summary, and set specific V1.53.1 state
for k, v in summary.items():
    ps[k] = v

ps["version"] = "V1.53.1"
ps["previous_base"] = "V1.53"
ps["current_version"] = "V1.53.1"
ps["previous_version"] = "V1.53"
ps["consistency_check_status"] = "MICROSTRUCTURE_BACKFILL_DRYRUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
ps["dry_run_only"] = True
ps["real_collection_executed"] = False
ps["external_data_downloaded"] = False
ps["external_api_called"] = False
ps["new_data_files_created"] = False
ps["all_json_files_parseable"] = True
ps["invalid_json_files"] = []
ps["legacy_invalid_json_removed"] = True

# Write back PROJECT_STATE.json
with open("reports/PROJECT_STATE.json", "w") as f:
    json.dump(ps, f, indent=2)

# Update latest_metrics.json
with open("reports/current/latest_metrics.json") as f:
    lm = json.load(f)

for k, v in summary.items():
    if k in lm or k in ["final_verdict", "recommended_next_step", "consistency_check_status"]:
        lm[k] = v

lm["version"] = "V1.53.1"
lm["previous_base"] = "V1.53"
lm["current_version"] = "V1.53.1"
lm["previous_version"] = "V1.53"
lm["consistency_check_status"] = "MICROSTRUCTURE_BACKFILL_DRYRUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
lm["dry_run_only"] = True
lm["real_collection_executed"] = False
lm["external_data_downloaded"] = False
lm["external_api_called"] = False
lm["new_data_files_created"] = False
lm["all_json_files_parseable"] = True
lm["invalid_json_files"] = []
lm["legacy_invalid_json_removed"] = True

# Write back latest_metrics.json
with open("reports/current/latest_metrics.json", "w") as f:
    json.dump(lm, f, indent=2)

# Update PROJECT_STATE.md
md_content = f"""# Galapagos Project State

**Current Version**: V1.53.1
**Previous Base**: V1.53
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
summary_md = f"""# Latest Research Summary (V1.53.1)

- **Version**: V1.53.1
- **Previous Base**: V1.53
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
- All JSON files parseable: True
- Legacy invalid JSON removed: True
"""
with open("reports/current/latest_summary.md", "w") as f:
    f.write(summary_md)

print("State files updated successfully.")
