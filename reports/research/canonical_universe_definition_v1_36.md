# Canonical Universe Definition - V1.36

```json
{
  "universe_name": "canonical_ev_strict_trade_universe",
  "universe_version": "V1.36",
  "base_data": {
    "predictions_path": "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet",
    "dataset_path": "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet",
    "intrabar_path": "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet"
  },
  "symbol": "BTC",
  "timeframe": "4h",
  "trade_unit_definition": "one unique trade opportunity per prediction row after canonical join",
  "join_policy": "inner",
  "dedup_policy": "DEDUP_EXACT_KEY_ONLY",
  "warmup_policy": "WARMUP_POLICY_EXPLICIT_NON_DROPPING",
  "outcome_policy": "OUTCOME_FRAME_SEPARATED",
  "reproducibility_policy": "FINGERPRINT_STRICT"
}
```
