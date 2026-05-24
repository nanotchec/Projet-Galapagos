# Max Historical Public Market Data V5.0

## Objectif

V5.0 etend les donnees marche publiques BTCUSDT 1m sur l'historique maximum complet disponible et documente. La fenetre retenue est `2023-03-25` -> `2026-05-23`, soit `1156` jours.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2023-03-25` -> `2026-05-23`
- Run : `v5_0_20260524T131602Z_5452c3f7`
- Premiere date disponible brute : `2017-08-17`
- Derniere date disponible brute : `2026-05-23`
- Dates manquantes : `0`

## Outputs

- 1m: `1664640` lignes, checksum `aa833956e85e6d92d1881366924c2ede1a935df26dfa3d35a7ec32c7b84682b2`
- 5m: `332928` lignes, checksum `7eaed34863699dcb73c30fb83722bdc5ac1b15cb6c43b0c2a6027a0826d5e363`
- 15m: `110976` lignes, checksum `24467f2873703b9ed69212d1dfe7722f1ee35bfcb2377267db95b2fa935428c0`
- 1h: `27744` lignes, checksum `20d44dbb8df47f09bed816dba3a5c458971e6ce8ead5f13d8e455053357780b1`

## Qualite

- 1m: gaps `0`, doublons `0`, parent-child `True`
- 5m: gaps `0`, doublons `0`, parent-child `True`
- 15m: gaps `0`, doublons `0`, parent-child `True`
- 1h: gaps `0`, doublons `0`, parent-child `True`

## Limitations

- V5.0 etend uniquement les donnees marche publiques BTCUSDT sur l'historique maximum disponible et documente.
- V5.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V5.0 ne valide aucune strategie.
V5.0 ne produit aucune feature.
V5.0 ne produit aucun label.
V5.0 ne produit aucun dataset ML.
V5.0 ne produit aucun modele ML.
V5.0 ne produit aucun backtest.
V5.0 ne produit aucun signal de trading.
V5.0 ne produit aucun ordre.
V5.0 n'autorise aucun paper live.
V5.0 n'autorise aucun trading reel.
