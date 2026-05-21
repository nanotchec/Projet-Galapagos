# Latest Summary

V3.0 est la dernière version validée par audit externe.

V3.1.4 est la candidate courante. Elle corrige uniquement l’ordre du smoke V3.1.4 : les validateurs sont lancés dans des subprocess séparés avant tout import `pandas`/`pyarrow` et avant toute lecture Parquet, sans changer les sorties fonctionnelles sous `data/research/v3_1/labels/forward_returns`.

V3.1.3 a été refusée en strict uniquement parce que le smoke importait et lisait les Parquet avant les subprocess de validateurs, causant un timeout. V3.1.4 conserve la séparation stricte avec les features V3.0 : aucune jointure features + labels, aucun dataset ML multi-day et aucun entraînement ML.

V3.1.4 reste `pending_external_audit`.

V3.1 ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.
