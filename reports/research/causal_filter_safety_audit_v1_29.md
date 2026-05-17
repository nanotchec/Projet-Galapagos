# Causal Filter Safety Audit V1 29

```json
{
  "filters": [
    {
      "filter_name": "prob_ge_0.55",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.6",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.65",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.7",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.55_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.55_per_1D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.6_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.6_per_1D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.65_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.65_per_1D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.7_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "first_ge_0.7_per_1D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "running_top_ge_0.55_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": true,
      "causal_status": "CAUSAL_FILTER_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
    },
    {
      "filter_name": "running_top_ge_0.6_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": true,
      "causal_status": "CAUSAL_FILTER_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
    },
    {
      "filter_name": "running_top_ge_0.65_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": true,
      "causal_status": "CAUSAL_FILTER_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
    },
    {
      "filter_name": "running_top_ge_0.7_per_7D",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": true,
      "causal_status": "CAUSAL_FILTER_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
    },
    {
      "filter_name": "prob_ge_0.6_cooldown_1 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.6_cooldown_3 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.6_cooldown_7 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.65_cooldown_1 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.65_cooldown_3 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    },
    {
      "filter_name": "prob_ge_0.65_cooldown_7 days 00:00:00",
      "decision_at_signal_time": true,
      "uses_future_scores": false,
      "uses_future_returns": false,
      "uses_realized_pnl": false,
      "uses_mfe_mae": false,
      "uses_exit_reason": false,
      "full_period_selection": false,
      "causal_status": "CAUSAL_FILTER_PASSED"
    }
  ]
}
```
