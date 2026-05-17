# Ev Net Baseline Interpretation - v1.38.2

```json
{
  "best_filter_observed": "filter_ev_gt_0",
  "best_filter_mean_net_pnl": -2.6852081489793344e-05,
  "best_filter_2026_mean_net_pnl": -0.00321872050730674,
  "beats_global_random_p95": false,
  "beats_monthly_random_p95": true,
  "baseline_interpretation": "Le filtre principal reste exploratoire: il bat la baseline monthly-count preserving mais pas la baseline globale, et il reste negatif sur le recent 2026 window. Le meilleur filtre global est inactif en 2026, donc il ne peut pas servir de candidat robuste sans diagnostic additionnel.",
  "chosen_due_to_recent_activity": true,
  "not_chosen_by_global_pnl_only": true,
  "top_global_pnl_filter": "filter_ev_top_quantile_causal",
  "top_global_pnl_filter_mean_net_pnl": 0.006775835866973116,
  "top_global_pnl_filter_recent_2026_selected_count": 0,
  "top_global_pnl_filter_recent_status": "RECENT_WINDOW_NO_SIGNALS",
  "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED"
}
```
