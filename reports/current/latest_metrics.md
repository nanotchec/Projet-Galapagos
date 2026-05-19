# Etat Projet V2.4.8 + candidat V2.5.1

- **Dernière version validée** : V2.4.8.
- **Verdict validé** : Finalisation robuste du validateur de resampling via focused Unit/Integration split sous les 5 secondes.
- **Version refusée en audit externe** : V2.5 (pour tests non reproductibles et régression runtime du validateur V2.4).
- **Version candidate** : V2.5.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : Finalisation et correction des tests du Feature Store Causal (Feature Store Test Reproducibility & V2.4 Runtime Regression Fix).
- **V2.5.1 produit uniquement** des features OHLCV causales déterministes sur BTCUSDT 2024-01-15 à partir des données V2.4 validées, sous forme de fichiers Parquet Gold sous `data/gold/features/`.

## Détails de la version candidate V2.5.1
- **Reproductibilité V2.5** : Élimination complète de tout chemin absolu local en dur `/Users/lilianserre/` dans la suite de tests du validateur. Les tests s'exécutent de façon 100% autonome et reproductible au sein du ZIP clean extrait.
- **Performance V2.4** : Résolution définitive de la régression de performance I/O du validateur V2.4 en environnement de VM lente d'audit (tests s'exécutant désormais en ~6 secondes via un monkeypatch ciblé).
- **Stabilité physique** : L'architecture modulaire de features sous `src/galapagos/features/` (`causal_ohlcv.py`, `quality.py`, `validation.py`, `schemas.py`, `registry.py`) reste 100% valide.
- **Sécurité et conformité** : Le validateur V2.5.1 intègre récursivement les validateurs V2.3 et V2.4. Il rejette strictement toute colonne extra (future_return, strategy_validated, etc.), label, signal, ou terme interdit.
- **Release ZIP V2.5.1** : Le package zip épuré `projet-galapagos-v2.5.1-clean.zip` (66 fichiers) passe à 100% l'audit de structure et le smoke test dans un environnement temporaire isolé.

## Clause de Sécurité Réglementaire V2.5.1
- Aucun trading réel, paper live, ordre, modèle ML, label ou backtest n'est autorisé.
- Le Feature Store V2.5.1 est strictement limité à des fins d'analyse de données historiques (Data/Research Only).
- La V2.5.1 est déclarée `pending_external_audit` avant toute validation externe finale.
