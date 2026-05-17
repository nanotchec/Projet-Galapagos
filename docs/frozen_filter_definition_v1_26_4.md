# Frozen Filter Definition - Galapagos V1.26.4

## Source Audit
La définition du filtre "Frozen" a été auditée directement depuis le code source et les rapports historiques.

- **Filtre identifié** : `low_frequency_strict_score`.
- **Source Code** : `src/galapagos/research/signal_selection/selection_rules.py`.
- **Logic** : `highest_score_per_period("7D")`.
- **Score Column** : `predicted_probability`.
- **Extraction Status** : SOURCE_MATCHED_CODE_AND_REPORTS.

## Paramètres du Filtre
- **Policy** : `horizon_only`.
- **Temporal Rule** : `7D` (Fenêtre hebdomadaire).
- **Tie-Break** : `pandas_current_order_after_score_sort` (Non-déterministe explicite).
- **Security Check** : Colonnes interdites vérifiées (pas d'utilisation de PnL futur).

## Avertissement sur le Tie-Break
L'implémentation historique ne définit pas de clé de tri secondaire explicite pour les scores égaux. Bien que le `groupby().head(1)` de pandas soit stable par rapport à l'ordre courant, cet ordre n'est pas garanti déterministe entre différentes exécutions ou versions de bibliothèques si des données arrivent dans un ordre différent.

Pour les validations futures, il est recommandé d'ajouter un tri explicite par `timestamp` croissant.
