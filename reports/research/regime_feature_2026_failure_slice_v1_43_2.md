# Regime Feature 2026 Failure Slice V1.43.2

Status: FAILURE_SLICE_2026_FEATURE_REGIME_PATTERN_FOUND

### Summary
```json
{
  "failure_slice_status": "FAILURE_SLICE_2026_FEATURE_REGIME_PATTERN_FOUND",
  "failure_threshold": -0.028940835169739776,
  "differentiating_features": [
    {
      "feature": "open_interest_bybit",
      "diff_score": 1.8597905825468148
    },
    {
      "feature": "open_interest",
      "diff_score": 1.8597905825468148
    },
    {
      "feature": "long_short_ratio_binance",
      "diff_score": -1.0102490614227329
    },
    {
      "feature": "long_short_ratio",
      "diff_score": -1.0102490614227329
    },
    {
      "feature": "cost_proxy_rebuilt",
      "diff_score": 0.9999794743377888
    },
    {
      "feature": "cost_proxy",
      "diff_score": 0.9999794743377888
    }
  ],
  "regime_patterns": {
    "regime_concentration": {
      "failure_dist": {
        "risk_on": 0.4839506172839506,
        "neutral": 0.36790123456790125,
        "risk_off": 0.14814814814814814
      },
      "overall_dist": {
        "risk_on": 0.45320197044334976,
        "neutral": 0.38571428571428573,
        "risk_off": 0.16108374384236454
      }
    }
  }
}
```