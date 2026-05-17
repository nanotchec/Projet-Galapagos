# Code Review V1.91

V1.91 audite les artefacts V1.84, V1.87 et V1.90 sans ecrire dans data/.
Le design V1.92 reste theorique, borne a cinq JSON et 50000 bytes.
Les controles anti-leakage imposent available_ts <= decision_ts, no-lookahead, provenance et checksums.
Aucun dataset n'est cree et aucune strategie n'est validee.
