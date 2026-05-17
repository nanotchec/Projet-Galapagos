# Recherche EV-Net canonique V1.38.1

V1.38.1 ne change pas la recherche EV-net de fond. Cette version corrige la cohérence entre l'état du projet, le rapport de release et les rapports de recherche.

Points corrigés :
- `previous_base = V1.38`.
- `PROJECT_STATE` est structuré avec deux blocs explicites :
  - `canonical_universe_context`.
  - `v1_38_research_context`.
- Les chemins de recommandation pointent vers `v1_38_1`.
- Le rapport de release passe à `release_ready_for_external_review = true` lorsque tous les contrôles sont verts.
- Le filtre EV-Net reste exploratoire seulement.

Rappels de garde-fous :
- aucune stratégie validée ;
- aucun paper live ;
- aucun ordre réel ;
- holdout non exécuté ;
- `evidence_classification = EXPLORATORY_ONLY`.

V1.38.2 ajoute ensuite une clarification de sémantique entre `release_ready_for_external_review` et la maturité scientifique de la stratégie.
