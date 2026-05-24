# Latest Metrics

- Dernière version validée : `V4.7`
- Candidate : `V4.8`
- Statut : `pending_external_audit`
- Direction : 1-year research decision gate and next roadmap

## Verdict V4.8

- Verdict : mitigé et non concluant.
- Recommandation principale : A. Étendre à l historique max OHLCV.
- Recommandation secondaire : E. Préparer une validation walk-forward offline.

## Baselines

- `logistic_regression` : bat souvent les baselines, mais résultat non concluant.
- `decision_tree_depth_2` : résultat faible à mitigé.

## Stabilité

- Aucun warning overfit train/validation/test pour les modèles appris selon le seuil V4.7.
- Warnings de concentration timeframe : `logistic_regression, decision_tree_depth_2`.
- Cas label shuffle sans avantage clair : `5`.

## Roadmap

- V5.0 : historique max OHLCV.
- V5.1 : features causales historique max.
- V5.2 : labels forward historique max.
- V5.3 : dataset offline et design walk-forward.
- V5.4 : ML offline et robustesse walk-forward/falsification.

## Safety

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
