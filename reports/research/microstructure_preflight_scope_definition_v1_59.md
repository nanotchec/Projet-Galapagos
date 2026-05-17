# Preflight Scope Definition (V1.59)

- Defines authorized planning perimeter.

```json
{
  "version": "V1.59",
  "current_version": "V1.59",
  "scope_name": "CONTROLLED_LOCAL_PREFLIGHT_PLANNING",
  "description": "Definition of boundaries and safety protocols for future local preflight dry-runs.",
  "preflight_executed": false,
  "preflight_plan_only": true,
  "authorized_activities": [
    "Manifest schema definition",
    "Network gate policy drafting",
    "Write gate policy drafting",
    "Stop condition definition",
    "Rollback procedure definition"
  ],
  "forbidden_activities": [
    "Real network connection",
    "Real data collection",
    "Data directory writes",
    "Real API calls",
    "Strategy validation"
  ],
  "evidence_classification": "INFRASTRUCTURE_ONLY",
  "status": "PLANNING_ONLY"
}
```
