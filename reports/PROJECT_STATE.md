# Etat du Projet : V8.0 validee + candidat V8.1

- **Derniere version validee** : V8.0.
- **Version candidate** : V8.1.
- **Statut candidate** : `PASS`.
- **Direction** : OHLCV + public trades 90-day research decision gate.

## Candidat V8.1

- Fenetre analysee : `2023-03-25` -> `2023-06-22`.
- Nombre de jours : `90`.
- Feature columns count V8.0 : `71`.
- Verdict : OHLCV + aggTrades 90 jours est interessant mais mitige et non concluant.
- Recommendation principale : A. Etendre les aggTrades a 1 an.
- Recommendation secondaire : D. Preparer une validation walk-forward offline plus stricte.
- Label shuffle no-clear-edge cases : `3`.
- Warnings concentration timeframe : `4`.
- Backtest recommande : `false`.

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
- V8.1 ne valide aucune strategie, aucun modele exploitable en trading et aucune rentabilite.
