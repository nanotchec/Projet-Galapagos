# Recent & Bull-Regime Diagnostic - V1.29.5 (Consistency Fix)

## Objectif du diagnostic
Corriger les incohérences méthodologiques de la V1.29.4 en s'assurant que tous les diagnostics sont effectués sur l'unité de trade dédupliquée (cohérente avec la V1.29.3, soit environ 225 trades).

## Changements V1.29.5
1. **Déduplication stricte** : La politique `first_stable_per_timestamp` est appliquée avant toute analyse.
2. **Standardisation des noms** : Utilisation systématique du suffixe `_diagnostic`.
3. **Prudence des Verdicts** :
   - Le statut de dépendance au régime est tempéré si la définition du régime est jugée "too coarse".
   - L'analyse du "cost drag" est marquée comme non isolée si les colonnes de coûts bruts sont absentes.
4. **Validateur de cohérence** : Un nouveau script vérifie que le `selected_count` final correspond aux attentes historiques.

## Résultats attendus
Une confirmation robuste de la dégradation récente de l'alpha sur un échantillon de trades propre et dédupliqué.

## Recommandations prioritaires
- Bloquer tout passage à la V1.30.
- Reprendre la recherche sur l'amélioration des signaux alpha.
