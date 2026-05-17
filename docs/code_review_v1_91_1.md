# Code Review V1.91.1

V1.91.1 corrige V1.91 en durcissant les seuils de validation.
Le design V1.92 reste theorique, borne a cinq JSON et 50000 bytes.
Les controles anti-leakage imposent available_ts <= decision_ts et no-lookahead strict.
Les audits de ZIP et smoke tests sont desormais obligatoires et verifies par le validateur.
