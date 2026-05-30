# Datacard V9.39 - OHLCV + AggTrades 5Y Dataset

## Statut

- Decision : `ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels`.
- Dataset cree : `False`.
- Target utilise : `None`.
- Qualite : `BLOCKED`.
- Couverture : `feature_store_ready_labels_missing`.

## Label readiness

Aucun label strictement compatible avec la fenetre 5Y `2021-05-05 -> 2026-05-05` n'a ete trouve.
V9.39 ne cree donc pas de faux dataset supervise et ne reutilise pas aveuglement les labels historiques.

## Limites

- Les labels V9.6/V9.12/V9.13 restent des candidats diagnostiques historiques sur une fenetre plus courte.
- V9.39 ne valide aucune strategie, aucun signal, aucun backtest et aucun modele.
- La suite recommandee est une label factory 5Y explicite avant tout dataset complet.
