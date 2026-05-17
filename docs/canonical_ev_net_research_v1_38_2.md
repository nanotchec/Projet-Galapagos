# Recherche EV-Net canonique V1.38.2

Cette note est conservée pour l’historique. La correction finale de sémantique d’interface est portée par V1.38.3.

V1.38.2 ne change pas la recherche EV-Net de fond. Cette version corrige uniquement la sémantique de reporting.

Points clarifiés :
- `consistency_check_status` est le champ principal de cohérence.
- `status`, s’il est conservé, doit lui être identique.
- `release_ready_for_external_review` décrit la qualité du paquet de revue externe.
- `strategy_reviewer_ready` décrit la maturité scientifique de la stratégie.
- Les deux notions ne doivent plus être confondues.

Rappels de garde-fous :
- aucune stratégie validée ;
- aucun paper live ;
- aucun ordre réel ;
- holdout non exécuté ;
- `evidence_classification = EXPLORATORY_ONLY`.
