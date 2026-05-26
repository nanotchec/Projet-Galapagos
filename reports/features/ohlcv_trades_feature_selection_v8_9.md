# OHLCV + Trades feature selection V8.9

- Selected features : `18`.
- Dropped features : `27`.
- Review features : `29`.
- Cette selection est une hypothese de recherche pour V9.0, pas une validation trading.
- V8.9 ne valide aucune strategie.
- V8.9 ne produit aucun backtest.
- V8.9 ne produit aucun signal de trading.
- V8.9 ne produit aucun ordre.

## Selected

- open
- high
- low
- close
- volume
- quote_volume
- trade_count_ohlcv
- agg_trade_count
- agg_trade_quantity_sum
- agg_trade_quote_quantity_sum
- agg_trade_vwap
- taker_buy_ratio_count
- taker_buy_ratio_quantity
- taker_imbalance_quantity
- agg_trades_per_minute
- trade_flow_pressure
- hour_utc
- day_of_week_utc

## Dropped

- taker_buy_base_volume_ohlcv
- taker_buy_quote_volume_ohlcv
- agg_trade_price_min
- agg_trade_price_max
- agg_trade_price_mean
- agg_trade_first_price
- agg_trade_last_price
- taker_buy_agg_count
- taker_sell_agg_count
- taker_buy_quantity
- taker_sell_quantity
- taker_buy_quote_quantity
- taker_sell_quote_quantity
- taker_buy_ratio_quote
- taker_imbalance_count
- taker_imbalance_quote
- agg_trade_count_vs_ohlcv_trade_count_ratio
- taker_imbalance_quantity_lag_1
- taker_imbalance_quantity_rolling_mean_15
- taker_imbalance_quantity_rolling_mean_60
- taker_imbalance_quantity_zscore_60
- intrabar_trade_price_range
- intrabar_last_to_first_return
- trade_flow_pressure_zscore_60
- warmup_row
- trades_feature_null_count
- trades_feature_error_count

## Review

- agg_trade_price_std
- agg_trade_price_change
- agg_trade_price_return
- agg_trade_quantity_mean
- agg_trade_quantity_std
- agg_trade_quantity_max
- agg_trade_large_trade_count
- agg_trade_large_trade_quantity_sum
- agg_quantity_per_minute
- agg_quote_quantity_per_minute
- avg_agg_trades_per_ohlcv_trade
- agg_quantity_vs_ohlcv_volume_ratio
- agg_quote_vs_ohlcv_quote_volume_ratio
- agg_trade_count_lag_1
- agg_trade_count_rolling_mean_5
- agg_trade_count_rolling_mean_15
- agg_trade_count_rolling_mean_60
- agg_trade_count_zscore_60
- agg_quantity_rolling_mean_5
- agg_quantity_rolling_mean_15
- agg_quantity_rolling_mean_60
- agg_quantity_zscore_60
- taker_buy_ratio_quantity_lag_1
- taker_buy_ratio_quantity_rolling_mean_15
- taker_buy_ratio_quantity_rolling_mean_60
- taker_buy_ratio_quantity_zscore_60
- intrabar_vwap_to_close
- intrabar_price_std_to_range
- is_weekend_utc
