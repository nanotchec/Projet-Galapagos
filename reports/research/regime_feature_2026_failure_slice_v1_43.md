# Regime Feature 2026 Failure Slice V1.43

Status: FAILURE_SLICE_2026_FEATURE_REGIME_PATTERN_FOUND

### Summary
```json
{
  "failure_slice_status": "FAILURE_SLICE_2026_FEATURE_REGIME_PATTERN_FOUND",
  "failure_threshold": -0.028940835169739776,
  "differentiating_features": [
    {
      "feature": "max_adverse_excursion_12bar",
      "diff_score": -1.736459336797934
    },
    {
      "feature": "open_interest_change_1",
      "diff_score": 1.6889497783250553
    },
    {
      "feature": "oi_change_1",
      "diff_score": 1.6889497783250553
    },
    {
      "feature": "open_interest_zscore_30d",
      "diff_score": 1.5956634564561054
    },
    {
      "feature": "oi_zscore_30d",
      "diff_score": 1.5956634564561054
    },
    {
      "feature": "derivatives_crowding_score",
      "diff_score": 1.3637964699461749
    },
    {
      "feature": "max_adverse_excursion_6bar",
      "diff_score": -1.2640288786395268
    },
    {
      "feature": "long_short_ratio_zscore",
      "diff_score": -1.2577508127833137
    },
    {
      "feature": "open_interest_change_3",
      "diff_score": 1.0390610206032795
    },
    {
      "feature": "oi_change_3",
      "diff_score": 1.0390610206032795
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