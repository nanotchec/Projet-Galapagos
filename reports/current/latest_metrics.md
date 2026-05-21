# Latest Metrics

- Dernière version validée : V3.3.1.
- Candidate : V3.4.1.
- Statut : `pending_external_audit`.
- Direction : multi-day ML robustness and falsification audit.
- Fenêtre : 2024-01-15 à 2024-01-21 inclus.
- Row counts datasets V3.2 : 1m `10080`, 5m `2016`, 15m `672`, 1h `168`.
- Score rows V3.3 : 1m `40196`, 5m `7940`, 15m `2564`, 1h `548`.
- Rows utilisées pour ML V3.3 : 1m `10049`, 5m `1985`, 15m `641`, 1h `137`.
- Target : `up_down_flat_h1`.
- Modèles : majority baseline, random seeded baseline, logistic regression, decision tree depth 2.
- Analyses V3.4 : baseline delta, split stability, timeframe stability, label shuffle falsification, feature leakage scan, metric forbidden scan.
- Correction V3.4.1 : bornes numériques strictes dans le validateur V3.4 pour refuser les métriques impossibles synchronisées manifest/report.
- Aucun edge robuste revendiqué.
- Aucun signal actionnable produit.
- Aucun modèle persistant.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun paper live.
- Aucun ordre.
- Aucun trading réel.

V3.4.1 est un audit research offline descriptif et falsifiable des baselines ML V3.3.1. Il ne valide aucun modèle exploitable en trading.
