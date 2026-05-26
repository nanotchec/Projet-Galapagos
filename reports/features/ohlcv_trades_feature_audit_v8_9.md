# OHLCV + Trades feature audit V8.9

## 1. Executive summary

- V8.9 audite et propose uniquement une selection/refactorisation de features OHLCV + aggTrades.
- V8.9 ne valide aucune strategie.
- V8.9 ne valide aucun modele exploitable en trading.
- V8.9 ne valide pas les features pour trading.
- V8.9 ne produit aucun backtest.
- V8.9 ne produit aucun signal de trading.
- V8.9 ne produit aucun ordre.
- La selection proposee est une hypothese de recherche pour V9.0.

## 2. Inputs

- Fenetre : `2023-03-25` -> `2024-03-24`.
- Total jours : `366`.
- Feature columns ML originales : `71`.
- V8.8 verdict : `interessant_mais_instable_non_concluant`.

## 3. Feature inventory

- Features inventoriees : `74`.
- Features autorisees ML : `71`.
- Comptage par famille : `{'audit': 3, 'microstructure_proxy': 6, 'ohlcv_base': 9, 'rolling_trade': 17, 'taker_flow': 12, 'temporal': 3, 'trade_aggregation': 17, 'trade_intensity': 7}`.

## 4. Missingness / warmup audit

- Timeframes audites : `['1m', '5m', '15m', '1h']`.
- Suspicious missingness : `{}`.

## 5. Variance / degeneracy audit

- Les constantes, quasi constantes et outliers extremes sont marques pour drop ou revue.

## 6. Collinearity audit

- Methode : `pearson`.
- Seuil high correlation : `0.95`.
- Paires fortement correlees : `97`.
- Clusters : `12`.

## 7. Feature family balance

- Families surrepresentees : `[]`.
- Families a refactoriser/fusionner : `[]`.

## 8. Candidate refined feature set

- Selected features : `18`.
- Dropped features : `27`.
- Review features : `29`.
- Selected : `['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trade_count_ohlcv', 'agg_trade_count', 'agg_trade_quantity_sum', 'agg_trade_quote_quantity_sum', 'agg_trade_vwap', 'taker_buy_ratio_count', 'taker_buy_ratio_quantity', 'taker_imbalance_quantity', 'agg_trades_per_minute', 'trade_flow_pressure', 'hour_utc', 'day_of_week_utc']`.
- Dropped : `['taker_buy_base_volume_ohlcv', 'taker_buy_quote_volume_ohlcv', 'agg_trade_price_min', 'agg_trade_price_max', 'agg_trade_price_mean', 'agg_trade_first_price', 'agg_trade_last_price', 'taker_buy_agg_count', 'taker_sell_agg_count', 'taker_buy_quantity', 'taker_sell_quantity', 'taker_buy_quote_quantity', 'taker_sell_quote_quantity', 'taker_buy_ratio_quote', 'taker_imbalance_count', 'taker_imbalance_quote', 'agg_trade_count_vs_ohlcv_trade_count_ratio', 'taker_imbalance_quantity_lag_1', 'taker_imbalance_quantity_rolling_mean_15', 'taker_imbalance_quantity_rolling_mean_60', 'taker_imbalance_quantity_zscore_60', 'intrabar_trade_price_range', 'intrabar_last_to_first_return', 'trade_flow_pressure_zscore_60', 'warmup_row', 'trades_feature_null_count', 'trades_feature_error_count']`.
- Review : `['agg_trade_price_std', 'agg_trade_price_change', 'agg_trade_price_return', 'agg_trade_quantity_mean', 'agg_trade_quantity_std', 'agg_trade_quantity_max', 'agg_trade_large_trade_count', 'agg_trade_large_trade_quantity_sum', 'agg_quantity_per_minute', 'agg_quote_quantity_per_minute', 'avg_agg_trades_per_ohlcv_trade', 'agg_quantity_vs_ohlcv_volume_ratio', 'agg_quote_vs_ohlcv_quote_volume_ratio', 'agg_trade_count_lag_1', 'agg_trade_count_rolling_mean_5', 'agg_trade_count_rolling_mean_15', 'agg_trade_count_rolling_mean_60', 'agg_trade_count_zscore_60', 'agg_quantity_rolling_mean_5', 'agg_quantity_rolling_mean_15', 'agg_quantity_rolling_mean_60', 'agg_quantity_zscore_60', 'taker_buy_ratio_quantity_lag_1', 'taker_buy_ratio_quantity_rolling_mean_15', 'taker_buy_ratio_quantity_rolling_mean_60', 'taker_buy_ratio_quantity_zscore_60', 'intrabar_vwap_to_close', 'intrabar_price_std_to_range', 'is_weekend_utc']`.

## 9. Leakage guard

- Passed : `True`.
- Forbidden selected features : `[]`.

## 10. Risks and limitations

- L'audit ne recalcule pas de nouvelles features.
- L'audit ne cree pas de dataset V9.0.
- L'audit n'entraine aucun modele ML.
- Les diagnostics V8.5/V8.7 ne permettent pas d'attribuer causalement l'instabilite a une feature precise.
- La selection proposee doit etre revalidee dans V9.0/V9.x.

## 11. Recommended V9.0 direction

- Construire un feature store raffine avec le set selectionne et les features en revue traitees explicitement.
- Revalider ensuite le dataset, le ML offline et le strict walk-forward.

## 12. Interdits maintenus

- Pas de trading.
- Pas de paper live.
- Pas d'ordre.
- Pas de nouveau dataset.
- Pas de modele ML.
- Pas de backtest.
- Pas de strategie.
- Pas de signal de trading.
- Pas de claim de rentabilite.
