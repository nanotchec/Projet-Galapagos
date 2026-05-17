# Code Review V1.91.3

V1.91.3 interdit les assertions tautologiques comme 'True is not False'.
Le validateur utilise 'ast' pour verifier l'absence de comparaisons triviales.
Le smoke test est desormais strictement borne pour eviter les timeouts.
Les audits de ZIP restent obligatoires et verifient la version correcte.
