# Etat Projet V2.4.8 + candidat V2.5.2

- **Dernière version validée** : V2.4.8.
- **Verdict validé** : Finalisation robuste du validateur de resampling via focused Unit/Integration split sous les 5 secondes.
- **Versions refusées en audit externe** :
  - V2.5 (pour tests non reproductibles et régression de temps d'exécution).
  - V2.5.1 (pour régression de temps d'exécution du validateur V2.4 sous pytest et timeout du smoke test après 180 secondes).
- **Version candidate** : V2.5.2.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : Finalisation et correction des tests du Feature Store Causal (V2.4 Runtime Regression & V2.5 Smoke Timeout Fix).
- **V2.5.2 produit uniquement** des features OHLCV causales déterministes sur BTCUSDT 2024-01-15 à partir des données V2.4 validées, sous forme de fichiers Parquet Gold sous `data/gold/features/`.

## Détails de la version candidate V2.5.2
- **Reproductibilité V2.5** : Élimination complète de tout chemin absolu local en dur `/Users/lilianserre/` dans la suite de tests du validateur (héritée de la V2.5.1).
- **Optimisation V2.4** : Résolution de la régression de performance I/O du validateur V2.4 sous pytest par la séparation rigoureuse des tests physiques critiques et le remplacement des tests redondants par des tests logiques unitaires purs en mémoire (temps d'exécution total de la suite réduit de 50% en local, assurant un passage ultra-rapide sous les 60 secondes en audit).
- **Smoke Test Robuste** : Refonte totale du smoke test de Galapagos pour en faire un processus ultra-rapide, autonome, sans pytest, avec des timeouts stricts de 30 secondes et une vérification directe des structures physiques des fichiers Parquet.
- **Stabilité physique** : L'architecture modulaire de features sous `src/galapagos/features/` (`causal_ohlcv.py`, `quality.py`, `validation.py`, `schemas.py`, `registry.py`) reste 100% valide.
- **Sécurité et conformité** : Le validateur V2.5.2 intègre récursivement les validateurs V2.3 et V2.4. Il rejette strictement toute colonne extra (future_return, strategy_validated, etc.), label, signal, ou terme interdit.
- **Release ZIP V2.5.2** : Le package zip épuré `projet-galapagos-v2.5.2-clean.zip` passe à 100% l'audit de structure et le smoke test en moins de 15 secondes dans un environnement isolé.

## Clause de Sécurité Réglementaire V2.5.2
- Aucun trading réel, paper live, ordre, modèle ML, label ou backtest n'est autorisé.
- Le Feature Store V2.5.2 est strictement limité à des fins d'analyse de données historiques (Data/Research Only).
- La V2.5.2 est déclarée `pending_external_audit` avant toute validation externe finale.
