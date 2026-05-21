# Latest Summary

V3.2.1 est la dernière version validée par audit externe.

V3.3.1 est la candidate courante. Elle conserve les baselines ML offline simples V3.3 sur le dataset supervisé multi-day V3.2, sur BTCUSDT du 2024-01-15 au 2024-01-21.

V3.3 a été refusée en strict uniquement parce que `tests/validation/test_multi_day_offline_ml_research_v3_3_validator.py` ne terminait pas proprement. V3.3.1 corrige uniquement le runtime des tests : le test nominal lance le validateur V3.3 dans un subprocess avec timeout, et la fixture ne relance plus le run ni le validateur dans le process pytest.

Les scores V3.3 sont écrits sous `data/research/v3_3/ml/offline_research` avec quatre timeframes : 1m `40196` lignes, 5m `7940` lignes, 15m `2564` lignes et 1h `548` lignes.

La cible unique est `up_down_flat_h1`. Les features sont limitées aux colonnes causales V3.0 autorisées. Les métriques sont descriptives et non actionnables.

V3.3 ne produit aucun modèle persistant, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.3.1 reste `pending_external_audit`.
