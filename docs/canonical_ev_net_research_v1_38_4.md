# Recherche EV-Net canonique V1.38.4

V1.38.4 ne change pas la recherche EV-Net de fond. Cette version retire le dernier champ legacy `status` du consistency check et garde `consistency_check_status` comme champ unique de statut principal.

Points clarifiés :
- `consistency_check_status` reste le statut principal ;
- `status_field_policy = REMOVED` ;
- `status_field_present = false` ;
- aucune stratégie validée ;
- aucun paper live ;
- aucun ordre réel ;
- holdout non exécuté ;
- `evidence_classification = EXPLORATORY_ONLY`.

Cette version ne modifie ni les métriques ni les filtres. Elle corrige uniquement une incohérence de reporting.
