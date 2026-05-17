# Ev Net Random Baselines - v1.38

```json
{
  "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
  "results": [
    {
      "filter_name": "filter_ev_gt_0",
      "baseline_type": "GLOBAL_SAME_COUNT",
      "observed_net_mean_pnl": -2.6852081489793344e-05,
      "random_p50": 0.0006238506089478995,
      "random_p95": 0.0006924715048710359,
      "beats_random_p95": false,
      "baseline_status": "COMPLETED"
    },
    {
      "filter_name": "filter_ev_gt_0",
      "baseline_type": "MONTHLY_COUNT_PRESERVING",
      "observed_net_mean_pnl": -2.6852081489793344e-05,
      "random_p50": -0.00010747659311819772,
      "random_p95": -8.092057083865425e-05,
      "beats_random_p95": true,
      "baseline_status": "COMPLETED"
    },
    {
      "filter_name": "filter_ev_gt_cost_buffer",
      "baseline_type": "GLOBAL_SAME_COUNT",
      "observed_net_mean_pnl": 0.00021918980864594277,
      "random_p50": 0.0006235392078228861,
      "random_p95": 0.0006966529912244983,
      "beats_random_p95": false,
      "baseline_status": "COMPLETED"
    },
    {
      "filter_name": "filter_ev_gt_cost_buffer",
      "baseline_type": "MONTHLY_COUNT_PRESERVING",
      "observed_net_mean_pnl": 0.00021918980864594277,
      "random_p50": 0.00019090424927742828,
      "random_p95": 0.0002472407094367378,
      "beats_random_p95": false,
      "baseline_status": "COMPLETED"
    },
    {
      "filter_name": "filter_ev_top_quantile_causal",
      "baseline_type": "GLOBAL_SAME_COUNT",
      "observed_net_mean_pnl": 0.006775835866973116,
      "random_p50": 0.0005685440398165146,
      "random_p95": 0.0011087690908110836,
      "beats_random_p95": true,
      "baseline_status": "COMPLETED"
    },
    {
      "filter_name": "filter_ev_top_quantile_causal",
      "baseline_type": "MONTHLY_COUNT_PRESERVING",
      "observed_net_mean_pnl": 0.006775835866973116,
      "random_p50": 0.0037720838411407108,
      "random_p95": 0.004339253676929106,
      "beats_random_p95": true,
      "baseline_status": "COMPLETED"
    }
  ]
}
```
