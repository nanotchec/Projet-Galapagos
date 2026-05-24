# Etat du Projet : V5.3 validee + correctif candidat V5.4.1

- **Derniere version validee** : V5.3.
- **Version candidate** : V5.4.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : audit-lite pytest collection packaging fix.

## Correctif V5.4.1

- V5.4.1 corrige uniquement le packaging audit-lite V5.4.
- Objectif : produire un ZIP auto-testable avec `PYTHONPATH=src python -m pytest --collect-only -q`.
- Les scores, datasets, features, labels et resultats ML V5.4 ne sont pas modifies.
- Les scripts historiques collectables par pytest et inutiles au ZIP V5.4 sont exclus.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- V5.4.1 reste non validee avant audit externe.
