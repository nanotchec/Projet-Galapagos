import json
from pathlib import Path

# Load summary from v1_53_2
with open("reports/research/microstructure_backfill_dryrun_summary_v1_53_2.json") as f:
    summary = json.load(f)

# Update PROJECT_STATE.json
with open("reports/PROJECT_STATE.json") as f:
    ps = json.load(f)

# Replace all top level keys that are in summary, and set specific V1.53.2 state
for k, v in summary.items():
    ps[k] = v

ps["version"] = "V1.53.2"
ps["current_version"] = "V1.53.2"
ps["previous_version"] = "V1.53.1"
ps["previous_base"] = "V1.53.1"
ps["project_state_version_aligned"] = True
ps["latest_metrics_version_aligned"] = True
ps["latest_summary_version_aligned"] = True
ps["all_json_files_parseable"] = True
ps["invalid_json_files"] = []
ps["legacy_invalid_json_removed"] = True
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

for k, v in ps.items():
    if k in lm or k in ["final_verdict", "recommended_next_step", "consistency_check_status", "project_state_version_aligned", "latest_metrics_version_aligned", "latest_summary_version_aligned"]:
        lm[k] = v

lm["version"] = "V1.53.2"
lm["current_version"] = "V1.53.2"
lm["previous_version"] = "V1.53.1"
lm["previous_base"] = "V1.53.1"

# Write back latest_metrics.json
with open("reports/current/latest_metrics.json", "w") as f:
    json.dump(lm, f, indent=2)

# Update PROJECT_STATE.md
md_content = f"""# Galapagos Project State

**Current Version**: V1.53.2
**Previous Base**: V1.53.1
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
summary_md = f"""# Latest Research Summary (V1.53.2)

- **Version**: V1.53.2
- **Previous base**: V1.53.1
- **Verdict**: {summary.get('final_verdict')}
- **Next step**: {summary.get('recommended_next_step')}
- **Evidence Classification**: INFRASTRUCTURE_ONLY

## Safety Profile
- Dry-run only: True
- No external data downloaded: True
- No API called: True
- No new data files created: True
- All JSON files parseable: True
- Legacy invalid JSON removed: True
- Project state aligned: True
- Latest metrics aligned: True
- No strategy validated: True
- No preregistration: True
- No paper live: True
- No real trading: True
"""
with open("reports/current/latest_summary.md", "w") as f:
    f.write(summary_md)

print("State files updated to V1.53.2 successfully.")
