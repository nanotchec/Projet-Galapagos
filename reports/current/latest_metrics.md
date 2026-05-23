# Latest Metrics

- Dernière version validée : `V4.5`
- Candidate : `V4.6`
- Statut : `pending_external_audit`
- Direction : 1-year offline ML research baselines

## Inputs V4.6

- Source datasets : dataset supervisé offline V4.5 validé.
- Source splits : splits temporels V4.5 validés.
- Fenêtre : `2024-01-01` à `2024-12-31` inclus.
- Timeframes : `1m`, `5m`, `15m`, `1h`.
- Target : `up_down_flat_h1`.
- Features autorisées : `31` colonnes causales.

## Row Counts Scores

- `1m` : `2108036`
- `5m` : `421508`
- `15m` : `140420`
- `1h` : `35012`

## Lignes ML Utilisées

- `1m` : `527009`
- `5m` : `105377`
- `15m` : `35105`
- `1h` : `8753`

## Splits ML Utilisés

- `1m` : train `316194`, validation `105408`, test `105407`
- `5m` : train `63214`, validation `21082`, test `21081`
- `15m` : train `21051`, validation `7027`, test `7027`
- `1h` : train `5240`, validation `1757`, test `1756`

## Qualité

- Target unique `up_down_flat_h1` : `true`
- Features interdites présentes : `0`
- Colonnes de sortie interdites : `0`
- Splits temporels sans shuffle : `true`
- `prediction_available_ts >= decision_ts` : `true`
- Schéma scores strict : `ML_SCORE_COLUMNS_V4_6`

## Safety

- ML offline V4.6 uniquement.
- Aucun modèle persistant.
- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
