# Expanded Public Market Data V3.5

## Objectif

V3.5 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 90 jours, du 2024-01-01 au 2024-03-30.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2024-01-01` -> `2024-03-30`
- Run : `v3_5_20260522T004929Z_f22dee56`

## Outputs

- 1m: `129600` lignes, checksum `2cbc7572304879c6a3c9df33e70a01acfce9831275039228ffa108ae55694771`
- 5m: `25920` lignes, checksum `55aaf60fd28ee34a3954f4c61ce1779999a09b26ff042e98bdcaf7273dc297bb`
- 15m: `8640` lignes, checksum `84aa841d1c6965d7e204c888f126a67155018432a47bb85c12683bdcf53fa68f`
- 1h: `2160` lignes, checksum `227e8bc0513f81b5971daf956d28934f57f89b57074f786b8973eec2d1d0e442`

## Qualite

- 1m: gaps `0`, doublons `0`, parent-child `True`
- 5m: gaps `0`, doublons `0`, parent-child `True`
- 15m: gaps `0`, doublons `0`, parent-child `True`
- 1h: gaps `0`, doublons `0`, parent-child `True`

## Limitations

- V3.5 etend uniquement les donnees marche publiques BTCUSDT sur une fenetre fixe de 90 jours.
- V3.5 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V3.5 ne valide aucune strategie.
V3.5 ne produit aucune feature.
V3.5 ne produit aucun label.
V3.5 ne produit aucun dataset ML.
V3.5 ne produit aucun modele ML.
V3.5 ne produit aucun backtest.
V3.5 ne produit aucun signal de trading.
V3.5 ne produit aucun ordre.
V3.5 n'autorise aucun paper live.
V3.5 n'autorise aucun trading reel.
