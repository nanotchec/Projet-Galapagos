# Résumé du Projet V2.5.1 (Feature Store Test Reproducibility & V2.4 Runtime Regression Fix)

- **Dernière version validée** : V2.4.8 (finalisation robuste du validateur de resampling via focused Unit/Integration split sous les 5 secondes).
- **Version refusée en audit** : V2.5 (en raison de tests validator non reproductibles utilisant un chemin absolu local et de la régression runtime du validateur V2.4).
- **Version candidate** : V2.5.1.
- **Statut candidate** : `pending_external_audit` (en attente de validation par audit externe).

## Synthèse technique de la V2.5.1
1. **Reproductibilité des tests V2.5** : La racine du projet est déterminée dynamiquement à partir de `__file__`, éliminant tout chemin absolu en dur `/Users/lilianserre/` dans la suite de tests du validateur. Les tests s'exécutent de façon totalement reproductible et isolée dans le ZIP clean.
2. **Performance du validateur V2.4** : Application d'un monkeypatch ciblé de l'ingestion publique V2.3 limitant les scans redondants du Parquet silver 1m lors des tests de mutation. La suite complète de 47 tests s'exécute désormais en environ 6 secondes au lieu de provoquer un timeout dans l'environnement d'audit.
3. **Feature Store Preview V2.5.1** : Produit uniquement des features OHLCV causales déterministes sur BTCUSDT 1m/5m/15m/1h à partir des données de marché V2.4.
4. **Zéro Trading, Zéro ML** : La version candidate ne contient aucune stratégie, aucun signal de trading, aucun modèle ML, aucun label, aucun backtest, aucun paper live, et n'autorise aucune exécution d'ordres ou utilisation d'API privées.
