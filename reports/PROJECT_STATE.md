# État du Projet : V2.5.2 validée + candidat V2.6

- **Dernière version validée** : V2.5.2 (Feature Store Causal).
- **Verdict validé** : Validation physique complète et rigoureuse du Feature Store Causal avec correction des régressions runtime V2.4 et résolution des timeouts de smoke test.
- **Versions antérieures validées** : V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.6.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : Clean Forward Label Factory Preview (V2.6) – Implémentation isolée de labels causaux et non-leakage.
- **V2.6 produit uniquement** des labels forward (prix futurs, simple/log returns, direction, up/down/flat ternaire) sur BTCUSDT 2024-01-15 à partir des données OHLCV V2.4 validées, sous forme de fichiers Parquet Gold sous `data/gold/labels/forward_returns/`.

---

## Détails de la version candidate V2.6

- **Isolation stricte** : Aucun mélange entre les features causales de la V2.5.2 et les labels de la V2.6. Les labels résident exclusivement dans `data/gold/labels/forward_returns/` et ne parasitent aucun silver Parquet.
- **Formule mathématique stricte** :
  - Simple returns et Log returns calculés sur 3 horizons temporels $h \in \{1, 3, 5\}$.
  - Direction ternaire (`1.0`, `-1.0`, `0.0`).
  - Classification Up/Down/Flat ternaire avec un seuil strict fixé à $0.0005$ ($0.05\%$).
- **Garantie anti-leakage temporel (Causal Separation)** :
  - `label_available_ts` correspond à la fin de l'horizon physique maximal ($h=5$).
  - Assertion stricte que pour chaque ligne valide, `label_available_ts > decision_ts`, garantissant qu'aucune décision ne dispose de look-ahead bias.
- **Gestion robuste des queues de séries** :
  - Les 5 dernières lignes de chaque fichier (pour $h=5$) sont marquées `tail_row = True`.
  - Toutes les colonnes de labels invalides associées à la queue de série sont **strictement nullifiées** (`NaN` / `None`), empêchant toute fausse interpolation ou contamination.
- **Validateur physique V2.6** :
  - Rejette strictement toute colonne de features V2.5 dans les labels.
  - Rejette toute colonne de labels dans les features V2.5 ou les Parquets silver V2.4.
  - Vérifie récursivement l'intégrité de toutes les versions précédentes (V2.3, V2.4, V2.5).
- **Performance de tests ultra-rapide** :
  - Les suites de tests de validation pytest (`test_clean_label_factory_v2_6_validator.py` et `test_forward_labels_v2_6.py`) s'exécutent entièrement en mémoire de façon isolée et passent à 100% en moins de 3 secondes.
- **Release ZIP V2.6** : Le package zip épuré `projet-galapagos-v2.6-clean.zip` (84 fichiers, 901 Ko) passe avec un succès complet l'audit de structure et les 5 commandes de smoke test en moins de 5 secondes dans un environnement isolé temporaire.

---

## Clause de Sécurité Réglementaire V2.6
- Aucun trading réel, paper live, ordre, modèle ML ou backtest n'est autorisé.
- La Label Factory V2.6 est strictement limitée à des fins d'analyse de données historiques (Data/Research Only).
- La V2.6 est déclarée `pending_external_audit` avant toute validation externe finale.
