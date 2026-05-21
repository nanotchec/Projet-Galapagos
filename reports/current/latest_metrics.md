# Latest Metrics

- Dernière version validée : V3.0.
- Candidate : V3.1.4.
- Statut : `pending_external_audit`.
- Direction : correction smoke-only avec validateurs isolés en subprocess avant tout import Parquet.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts labels V3.1 : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Horizons : `[1, 3, 5]`.
- Threshold : `0.0005`.
- Aucun dataset ML V3.1.
- Aucun modèle ML V3.1.
- Aucun backtest.
- Aucune stratégie.
- Aucun paper live.
- Aucun ordre.
- Aucun trading réel.

V3.1.3 a été refusée en strict uniquement parce que le smoke importait et lisait les Parquet avant les subprocess de validateurs, causant un timeout. V3.1.4 ne change pas le fond fonctionnel des labels.
