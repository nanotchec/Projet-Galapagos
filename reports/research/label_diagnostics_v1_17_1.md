# Label Diagnostics v1.17.1

Verdict: **LABELS_STABLE**
Status: partial

> target_up_after_cost_* columns were absent. Synthesised from forward_return with fixed cost thresholds.

### Label Base Rates by Year
**target_up_after_cost_6bar**
- 2024: 49.18%
- 2025: 46.35%
- 2026: 44.72%
**target_up_after_cost_12bar**
- 2024: 50.14%
- 2025: 45.21%
- 2026: 45.14%

## Raw Payload
```json
{
  "version": "v1.17.1",
  "status": "partial",
  "verdict": "LABELS_STABLE",
  "label_analysis": {
    "target_up_after_cost_6bar": {
      "2024": {
        "base_rate": 0.4918032786885246,
        "count": 2196
      },
      "2025": {
        "base_rate": 0.4634703196347032,
        "count": 2190
      },
      "2026": {
        "base_rate": 0.44722222222222224,
        "count": 720
      }
    },
    "target_up_after_cost_12bar": {
      "2024": {
        "base_rate": 0.5013661202185792,
        "count": 2196
      },
      "2025": {
        "base_rate": 0.4520547945205479,
        "count": 2190
      },
      "2026": {
        "base_rate": 0.4513888888888889,
        "count": 720
      }
    }
  },
  "partial_note": "target_up_after_cost_* columns were absent. Synthesised from forward_return with fixed cost thresholds."
}
```