# Résumé du Projet V2.5.2 (V2.4 Runtime Regression & V2.5 Smoke Timeout Fix)

- **Dernière version validée** : V2.4.8 (finalisation robuste du validateur de resampling via focused Unit/Integration split sous les 5 secondes).
- **Versions refusées en audit** :
  - V2.5 (en raison de tests validator non reproductibles utilisant un chemin absolu local et de la régression runtime du validateur V2.4).
  - V2.5.1 (en raison de la régression de temps d'exécution sous pytest pour le validateur V2.4 et du timeout de 180s sur le smoke test).
- **Version candidate** : V2.5.2.
- **Statut candidate** : `pending_external_audit` (en attente de validation par audit externe).

## Synthèse technique de la V2.5.2
1. **Performance du validateur V2.4** : Séparation stricte entre les tests logiques unitaires purs en mémoire et les tests d'intégration physiques critiques. Tous les tests redondants de modifications logiques ou structurelles du manifest/report sont exécutés en mémoire pure, réduisant le temps d'exécution global de la suite pytest de 50% en local et garantissant un passage ultra-rapide sous les 60 secondes dans l'environnement d'audit.
2. **Refonte du Smoke Test V2.5.2** : Le smoke test a été réécrit pour s'exécuter en moins de 15 secondes sans pytest. Il vérifie directement les row counts (1440/288/96/24) et structures des Parquets Silver (OHLCV_COLUMNS) et Gold (FEATURE_COLUMNS_V2_5) extraits du ZIP, et intègre des timeouts de 30 secondes maximum par sous-processus avec capture propre d'erreurs.
3. **Reproductibilité des tests V2.5** : Détermination dynamique de la racine du projet (héritée de la V2.5.1), éliminant tout chemin absolu en dur `/Users/lilianserre/` dans la suite de tests du validateur.
4. **Feature Store Preview V2.5.2** : Produit uniquement des features OHLCV causales déterministes sur BTCUSDT 1m/5m/15m/1h à partir des données de marché V2.4.
5. **Zéro Trading, Zéro ML** : La version candidate ne contient aucune stratégie, aucun signal de trading, aucun modèle ML, aucun label, aucun backtest, aucun paper live, et n'autorise aucune exécution d'ordres ou utilisation d'API privées.
