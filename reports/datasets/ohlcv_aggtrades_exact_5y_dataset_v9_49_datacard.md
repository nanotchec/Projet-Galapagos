# Datacard V9.49 - Dataset OHLCV + AggTrades 5Y

## Objet
Dataset supervise offline construit a partir du feature store combine V9.47 valide V9.48 et des labels V9.40.

## Fenetre
- Fenetre : `2021-05-05 -> 2026-05-05`.
- Target principal : `up_down_flat_volnorm_h1_5y`.
- Splits temporels : train 60 %, validation 20 %, test 20 %, shuffle false.
- Walk-forward group : `calendar_month`.
- Purge/embargo : `none_v9_49_preview`.

## Lignes
- `1m` : rows `2630880`, valides target `2630395`, invalides `485`.
- `5m` : rows `526176`, valides target `526104`, invalides `72`.
- `15m` : rows `175392`, valides target `175328`, invalides `64`.
- `1h` : rows `43848`, valides target `43787`, invalides `61`.

## Causalite
- Leakage guard : `PASS`.
- Les features doivent etre disponibles avant ou a `decision_ts`.
- Les labels valides doivent etre disponibles strictement apres `decision_ts`.
- Les labels diagnostics sont conserves comme colonnes d'audit, pas comme features.

## Limites
- Ce dataset ne valide aucun edge, aucune strategie et aucun signal.
- Aucun ML, walk-forward, backtest, PnL, Sharpe, drawdown ou modele persistant n'est produit.
- Les lignes warmup/tail sans target H1 valide sont conservees avec `row_valid_for_dataset=false`.

## Decision
- Decision V9.49 : `combined_features_5y_dataset_created`.
- Qualite : `PASS`.
- Couverture : `target_5y_dataset_window_complete`.
