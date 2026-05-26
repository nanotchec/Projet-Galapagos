# Etat du Projet : V8.6 validee + candidat V8.7

- **Derniere version validee** : V8.6.
- **Version candidate** : V8.7.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : strict walk-forward offline validation.

## Candidat V8.7

- Fenetre : `2023-03-25` -> `2024-03-24`.
- Nombre de jours : `366`.
- Feature columns : `71`.
- Folds par timeframe : `{'1m': 5, '5m': 5, '15m': 5, '1h': 5}`.
- Scores par timeframe : `{'1m': 8805440, '5m': 1759808, '15m': 585536, '1h': 145184}`.
- Validation offline uniquement, sans backtest.

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
- V8.7 reste non validee avant audit externe.
