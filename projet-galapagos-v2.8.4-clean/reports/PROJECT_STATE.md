# État du Projet : V2.7.2 validée + candidat V2.8.4

- **Dernière version validée** : V2.7.2 (Offline Supervised Dataset).
- **Versions antérieures validées** : V2.6.2 (Clean Label Factory), V2.5.2 (Feature Store Causal), V2.4.8 (Resampling OHLCV Silver), V2.3.1 (Ingestion Raw).
- **Version candidate** : V2.8.4.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : offline ML validator runtime and smoke timeout finalization.

## Candidat V2.8.4

- V2.8 entraîne des baselines ML offline simples sur les datasets supervisés V2.7 déjà validés.
- V2.8 a été refusée en strict parce que les scripts release/audit n'étaient pas autonomes dans le ZIP clean et parce que le garde-fou artefacts ML/backtest était incomplet.
- V2.8.1 ne change pas les modèles ni les métriques : elle durcit l'autonomie release/audit et interdit les artefacts persistants `model.pkl`, `model.joblib`, backtests, stratégies, ordres et exécution.
- V2.8.1 a été refusée en strict uniquement parce que le fichier complet de tests du validateur V2.8 restait trop lent en audit externe.
- V2.8.2 finalise le runtime de tests en remplaçant les validations complètes inutiles par des helpers ciblés, sans relâcher le validateur de production.
- V2.8.2 a été refusée en strict parce que certains tests de mutation score restaient trop coûteux en audit externe et parce que le smoke capturait un gros JSON de validation ML.
- V2.8.3 a été refusée en strict parce que le test nominal relançait encore une validation complète et parce que le smoke appelait encore les validateurs via subprocess.
- V2.8.4 finalise le runtime du test nominal et des tests score, puis rend le smoke silencieux via appels directs aux validateurs.
- Les modèles autorisés sont bornés : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- La cible unique est `up_down_flat_h1`.
- Les métriques produites sont descriptives et non actionnables.
- V2.8 ne valide aucune stratégie et ne transforme aucun score en signal.
- V2.8 produit des artefacts de recherche offline uniquement.
- V2.8.4 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun signal de trading.
- Aucun backtest.
- Aucune API privée.
- Aucune clé API.
- Aucun modèle n'est validé pour une exploitation trading.
- Aucun modèle persistant n'est produit.
- V2.8.4 reste non validée avant audit externe.
