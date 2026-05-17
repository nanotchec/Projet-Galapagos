# Recherche EV-Net canonique V1.38.3

V1.38.3 ne change pas la recherche EV-Net de fond. Cette version corrige uniquement la sémantique de reporting.

Points clarifiés :
- `consistency_check_status` est le champ principal de cohérence.
- `status`, s’il existe encore dans un artefact legacy, doit lui être identique.
- `ready_for_reviewer` est supprimé des états et métriques courants.
- `release_ready_for_external_review` décrit la qualité du paquet de revue externe.
- `strategy_reviewer_ready` décrit la maturité scientifique de la stratégie.

Rappels de garde-fous :
- aucune stratégie validée ;
- aucun paper live ;
- aucun ordre réel ;
- holdout non exécuté ;
- `evidence_classification = EXPLORATORY_ONLY`.

Note de continuité :
- V1.38.4 retire ensuite le dernier champ legacy `status` du consistency check et garde `consistency_check_status` comme champ unique.
