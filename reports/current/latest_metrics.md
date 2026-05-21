# Latest Metrics

- Dernière version validée : V3.0.
- Candidate : V3.1.5.
- Statut : `pending_external_audit`.
- Direction : correction smoke-only avec logs hors du root extrait.
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

V3.1.4 a été refusée en strict uniquement parce que le smoke écrivait ses logs dans le root extrait du ZIP, polluant les validateurs suivants. V3.1.5 ne change pas le fond fonctionnel des labels.
