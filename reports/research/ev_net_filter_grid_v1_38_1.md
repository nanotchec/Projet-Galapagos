# Ev Net Filter Grid - v1.38.1

```json
{
  "filters_tested": [
    {
      "filter_name": "filter_ev_gt_0",
      "family": "EV_BASIC",
      "description": "Net Expected Value > 0",
      "causal_status": "CAUSAL_PAST_PAYOFFS",
      "eligible_for_ranking": true,
      "exclusion_reason": null,
      "uses_future_info": false,
      "uses_full_period_statistic": false,
      "requires_warmup": true,
      "selection_columns_used": [
        "ev_calibrated_proxy"
      ]
    },
    {
      "filter_name": "filter_ev_gt_cost_buffer",
      "family": "EV_BUFFERED",
      "description": "Net Expected Value > 10bps Cost Proxy",
      "causal_status": "CAUSAL_PAST_PAYOFFS",
      "eligible_for_ranking": true,
      "exclusion_reason": null,
      "uses_future_info": false,
      "uses_full_period_statistic": false,
      "requires_warmup": true,
      "selection_columns_used": [
        "ev_calibrated_proxy",
        "cost_proxy"
      ]
    },
    {
      "filter_name": "filter_prob_65_ev_pos",
      "family": "PROB_EV_HYBRID",
      "description": "Calibrated Prob >= 0.65 AND Net EV > 0",
      "causal_status": "CAUSAL_HYBRID",
      "eligible_for_ranking": true,
      "exclusion_reason": null,
      "uses_future_info": false,
      "uses_full_period_statistic": false,
      "requires_warmup": true,
      "selection_columns_used": [
        "predicted_probability_calibrated",
        "ev_calibrated_proxy"
      ]
    },
    {
      "filter_name": "filter_ev_top_quantile_non_causal",
      "family": "EV_QUANTILE",
      "description": "Top 10% EV (Full Period Quantile)",
      "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE",
      "eligible_for_ranking": false,
      "exclusion_reason": "full_period_quantile_non_causal",
      "uses_future_info": true,
      "uses_full_period_statistic": true,
      "requires_warmup": false,
      "selection_columns_used": [
        "ev_calibrated_proxy"
      ]
    },
    {
      "filter_name": "filter_ev_top_quantile_causal",
      "family": "EV_QUANTILE",
      "description": "Top 10% EV (Expanding Past Quantile)",
      "causal_status": "CAUSAL_EXPANDING_PAST_QUANTILE",
      "eligible_for_ranking": true,
      "exclusion_reason": null,
      "uses_future_info": false,
      "uses_full_period_statistic": false,
      "requires_warmup": true,
      "selection_columns_used": [
        "ev_calibrated_proxy"
      ]
    }
  ],
  "eligible_filters": [
    "filter_ev_gt_0",
    "filter_ev_gt_cost_buffer",
    "filter_prob_65_ev_pos",
    "filter_ev_top_quantile_causal"
  ],
  "excluded_filters": [
    "filter_ev_top_quantile_non_causal"
  ],
  "exclusion_reasons": {
    "filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"
  },
  "causal_filter_count": 4,
  "non_causal_filter_count": 1,
  "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED"
}
```
