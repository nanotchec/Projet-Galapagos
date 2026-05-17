# V1.45 Ablation Results

- Experiments completed: 5

## Data Preview

```json
{
  "results": [
    {
      "experiment_name": "all_allowed_features",
      "feature_count": 112,
      "pre_2026_score": 0.6112000000000001,
      "recent_2026_score": 0.49560000000000004,
      "score_delta": -0.11560000000000004,
      "downside_capture_proxy": 0.5,
      "stability_score": 0.4,
      "interpretation": "Weak signal.",
      "result_status": "FEATURE_ABLATION_RESULTS_COMPLETE"
    },
    {
      "experiment_name": "raw_only",
      "feature_count": 12,
      "pre_2026_score": 0.5512,
      "recent_2026_score": 0.5106,
      "score_delta": -0.04059999999999997,
      "downside_capture_proxy": 0.5,
      "stability_score": 0.8,
      "interpretation": "Exploratory signal observed.",
      "result_status": "FEATURE_ABLATION_RESULTS_COMPLETE"
    },
    {
      "experiment_name": "alpha_only",
      "feature_count": 22,
      "pre_2026_score": 0.6022000000000001,
      "recent_2026_score": 0.4911,
      "score_delta": -0.11110000000000009,
      "downside_capture_proxy": 0.45,
      "stability_score": 0.4,
      "interpretation": "Weak signal.",
      "result_status": "FEATURE_ABLATION_RESULTS_COMPLETE"
    },
    {
      "experiment_name": "raw_without_microstructure",
      "feature_count": 89,
      "pre_2026_score": 0.5589000000000001,
      "recent_2026_score": 0.51445,
      "score_delta": -0.0444500000000001,
      "downside_capture_proxy": 0.5,
      "stability_score": 0.8,
      "interpretation": "Exploratory signal observed.",
      "result_status": "FEATURE_ABLATION_RESULTS_COMPLETE"
    },
    {
      "experiment_name": "raw_plus_regime_interactions",
      "feature_count": 12,
      "pre_2026_score": 0.5512,
      "recent_2026_score": 0.5106,
      "score_delta": -0.04059999999999997,
      "downside_capture_proxy": 0.5,
      "stability_score": 0.8,
      "interpretation": "Exploratory signal observed.",
      "result_status": "FEATURE_ABLATION_RESULTS_COMPLETE"
    }
  ]
}
```