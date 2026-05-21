# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1 est la candidate courante et construit uniquement une label factory forward multi-day à partir des OHLCV V2.9 validés. Les sorties sont isolées sous `data/research/v3_1/labels/forward_returns` avec les row counts attendus `10080 / 2016 / 672 / 168`.

V3.1 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

V3.1 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
