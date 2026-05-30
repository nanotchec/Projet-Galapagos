# V9.40 - OHLCV + AggTrades 5Y Label Factory

## Resume
- Decision V9.40 : `ohlcv_aggtrades_5y_labels_created_with_warnings`.
- Recommandation suivante : `V9.41 - OHLCV + AggTrades 5Y Dataset`.
- Labels crees : `True`.
- Dataset supervise cree : `False`.
- Label principal selectionne : `up_down_flat_volnorm_h1_5y`.
- Qualite : `PASS_WITH_WARNINGS`.
- Couverture : `target_5y_label_window_complete`.
- Leakage guard : `PASS`.

## Row counts
- `1m` : `2630880` lignes.
- `5m` : `526176` lignes.
- `15m` : `175392` lignes.
- `1h` : `43848` lignes.

## Distributions principales
- `1m` : `{'-1': 508675, '0': 1611217, '1': 510503}`, flat_ratio `0.612538`.
- `5m` : `{'-1': 94941, '0': 335990, '1': 95173}`, flat_ratio `0.638638`.
- `15m` : `{'-1': 30190, '0': 114565, '1': 30573}`, flat_ratio `0.653432`.
- `1h` : `{'-1': 7092, '0': 29475, '1': 7220}`, flat_ratio `0.673145`.

## Limites
- Ces labels sont des candidats descriptifs causaux. Ils ne prouvent aucun edge robuste.
- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.
- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
