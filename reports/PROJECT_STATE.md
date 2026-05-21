# État du Projet : V3.3.1 validée + candidat V3.4.1

- **Dernière version validée** : V3.3.1.
- **Versions antérieures validées** : V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.4.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : multi-day ML robustness and falsification audit.

## Candidat V3.4.1

- V3.4 audite uniquement la robustesse descriptive et la falsification des baselines ML offline V3.3.1.
- V3.4 a été refusée en strict parce que des métriques impossibles synchronisées entre manifest et report JSON étaient acceptées.
- V3.4.1 durcit le validateur en bornant les métriques numériques V3.4.
- Analyses : `baseline_delta`, `split_stability`, `timeframe_stability`, `label_shuffle_falsification`, `feature_leakage_scan`, `metric_forbidden_scan`.
- Scores research V3.3 : 1m `40196`, 5m `7940`, 15m `2564`, 1h `548`.
- V3.4 ne revendique aucun edge robuste et ne produit aucun signal actionnable.
- Aucun modèle persistant n’est écrit.
- V3.4.1 ne produit aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.4.1 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun modèle persistant.
- Aucune API privée.
- Aucune clé API.
- V3.4.1 reste non validée avant audit externe.
