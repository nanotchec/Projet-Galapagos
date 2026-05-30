# V9.39 - OHLCV + AggTrades 5Y Dataset

## Resume
- Decision V9.39 : `ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels`.
- Recommandation suivante : `V9.40 - OHLCV + AggTrades 5Y Label Factory`.
- Dataset cree : `False`.
- Label readiness : `MISSING_5Y_COMPATIBLE_LABELS`.
- Target utilise : `None`.
- Qualite : `BLOCKED`.
- Couverture : `feature_store_ready_labels_missing`.

## Labels
- `max_history_v5_2` : disponible `True`, fenetre `2023-03-25 -> 2026-05-23`, compatible 5Y `False`, target `None`.
- `volnorm_v9_6` : disponible `True`, fenetre `2023-03-25 -> 2024-03-24`, compatible 5Y `False`, target `up_down_flat_volnorm_h1`.
- `horizon_event_v9_12` : disponible `True`, fenetre `2023-03-25 -> 2024-03-24`, compatible 5Y `False`, target `up_down_flat_volnorm_h4`.
- `h4_dataset_v9_13` : disponible `True`, fenetre `2023-03-25 -> 2024-03-24`, compatible 5Y `False`, target `up_down_flat_volnorm_h4`.
- `v9_11_failure_analysis` : disponible `True`, fenetre `2023-03-25 -> 2024-03-24`, compatible 5Y `False`, target `None`.

## Garde-fous
- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.
- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
