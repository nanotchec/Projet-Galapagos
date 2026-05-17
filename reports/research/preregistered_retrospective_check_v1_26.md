# Preregistered Retrospective Check V1 26

```json
{
  "check_type": "retrospective",
  "not_out_of_sample": true,
  "multiple_testing_risk_present": true,
  "cannot_validate_strategy": true,
  "checks": {
    "mean_net_pnl_positive": {
      "passed": true,
      "evidence": 0.007856600971404403
    },
    "beats_monthly_random_p95": {
      "passed": true,
      "evidence": 0.0020884839833784567
    },
    "recent_window_robust": {
      "passed": true,
      "evidence": 0.0063011115079344366
    },
    "sample_size_recent": {
      "passed": false,
      "evidence": 17
    },
    "concentration_check": {
      "passed": false,
      "evidence": 0.6165574626293503
    },
    "overfit_risk_low": {
      "passed": false,
      "evidence": 78
    }
  },
  "verdict": "RETROSPECTIVE_CHECK_PROMISING_BUT_FAILS_ROBUSTNESS"
}
```