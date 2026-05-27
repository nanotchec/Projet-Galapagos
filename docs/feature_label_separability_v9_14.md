# V9.14 - Feature/Label Separability Diagnostic & Next Branch Decision

## Executive summary
- Decision : `feature_first_before_more_labels`.
- Justification : Les labels h4 restent proches du shuffle et les features ne montrent pas une separabilite commune stable entre timeframes.
- V9.14 est une analyse descriptive offline, pas un walk-forward et pas un backtest.
- Aucun trading, aucun paper live, aucun ordre, aucune strategie, aucun signal actionnable.

## Diagnostic labels V9.13
- Target : `up_down_flat_volnorm_h4`.
- Donnees full lues en read-only : `True`.
- FLAT trop faible : `['1m']`.
- FLAT trop eleve : `['1h']`.

## Diagnostic ML V9.13
- Decision ML : `h4_offline_ml_completed_but_close_to_shuffled_labels`.
- Clear wins vs baselines : `0`.
- Cas proches des labels melanges : `14`.
- Collapses de classes detectes : `33`.

## Separabilite features/labels
- Methode : `eta_squared_and_standardized_class_mean_range_by_feature`.
- Top features communes entre timeframes : `[]`.
- Top features instables : `['agg_trade_count', 'agg_trade_quote_quantity_sum', 'agg_trade_vwap', 'agg_trades_per_minute', 'close', 'high', 'low', 'open', 'quote_volume', 'trade_count_ohlcv']`.

## Hypotheses
- `H1` label encore mal defini : `high` - 14 cas restent trop proches des labels melanges.
- `H2` features actuelles insuffisantes : `high` - clear wins=0, top features communes=0.
- `H3` horizon h4 pas adapte : `medium` - Le h4 ameliore legerement la distance aux labels melanges mais reste insuffisant.
- `H4` multi-classe DOWN/FLAT/UP trop difficile : `medium` - Les distributions extremes du FLAT en 1m et 1h persistent.
- `H5` fenetre 2023-2024 trop limitee : `medium` - La stabilite regime/fenetre reste non prouvee sans extension de donnees.
- `H6` OHLCV+trades agreges peu informatifs : `high` - top features instables=10.
- `H7` extension data/features avant nouveau label : `high` - Les labels h1 puis h4 ne rendent pas les modeles clairement falsifiables.
- `H8` arret de branche refined labels : `medium` - Plusieurs redesign labels successifs restent proches du shuffle; arret possible si feature/data-first echoue.

## Recommandation suivante
- V9.15 Feature Separability / Feature Refinement Candidate.
- Aucun backtest n'est recommande a ce stade.

## Interdits maintenus
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest execute.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- Aucun sidecar et aucune empreinte ZIP.
