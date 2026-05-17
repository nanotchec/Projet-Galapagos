# Intrabar Execution Simulation v1.18.2

Verdict: **INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER**

## JSON Payload
```json
{
  "simulation_input_type": "real_signal_timestamps_with_artificial_exit_assumptions",
  "is_real_trade_simulation": false,
  "signal_timestamp_source": "ml_predictions",
  "signal_timestamp_type": "real_oos_model_prediction_timestamps",
  "trade_parameter_source": "artificial_assumptions",
  "entry_price_source": "intrabar_open",
  "stop_loss_source": "fixed_minus_5pct_placeholder",
  "take_profit_source": "fixed_plus_5pct_placeholder",
  "side_source": "predicted_label_long_only_or_default_long",
  "raw_signal_rows": 23426,
  "unique_signal_timestamps": 4275,
  "duplicate_signal_rows": 19151,
  "duplicates_per_timestamp_max": 20,
  "models_count": 3,
  "selected_signal_policy": "max_predicted_probability",
  "evaluated_signal_count": 70,
  "artificial_exit_assumptions": true,
  "ambiguous_count": 0,
  "verdict": "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
  "note": "Timestamps are from ML predictions, but exits are placeholder assumptions."
}
```
