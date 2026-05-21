# Latest Metrics

- Dernière version validée : V3.0.
- Candidate : V3.1.6.
- Statut : `pending_external_audit`.
- Direction : correction smoke/test-only avec isolation par validateur.
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

V3.1.5 a été refusée en strict parce que le smoke lançait tous les validateurs sur le même root extrait, provoquant encore un timeout sur V2.8. V3.1.6 ne change pas le fond fonctionnel des labels.
