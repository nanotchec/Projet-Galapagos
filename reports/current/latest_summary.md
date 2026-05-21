# Latest Summary

V3.1.10 est la dernière version validée par audit externe.

V3.2 est la candidate courante. Elle assemble un dataset supervisé offline multi-day à partir des features causales V3.0 et des labels forward V3.1, sur BTCUSDT du 2024-01-15 au 2024-01-21.

Les outputs V3.2 sont écrits sous `data/research/v3_2/datasets/offline_supervised` avec quatre timeframes : 1m `10080` lignes, 5m `2016` lignes, 15m `672` lignes et 1h `168` lignes. Les splits sont temporels, sans shuffle : train 60 %, validation 20 %, test 20 %.

V3.2 ne produit aucun ML V3.2, aucun modèle ML V3.2, aucun backtest, aucune stratégie, aucun paper live, aucun ordre et aucun trading réel.

V3.2 reste `pending_external_audit`.
