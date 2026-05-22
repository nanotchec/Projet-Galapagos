# Expanded Public Market Data V3.5

Note V3.5.2 : correction strictement runtime raw-to-1m. Les donnees OHLCV V3.5 restent identiques ; V3.5.2 vectorise la verification par date sans creer de features, labels, dataset ML, ML, backtest, strategie ou ordre.

## Objectif

V3.5 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 90 jours, du 2024-01-01 au 2024-03-30.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2024-01-01` -> `2024-03-30`
- Run : `v3_5_20260522T085438Z_36f1db8e`

## Outputs

- 1m: `129600` lignes, checksum `8f69693df4023fc65eeb473ab6fac443329d872e64887cdfe102d874ced66a50`
- 5m: `25920` lignes, checksum `1d7350248c56502a4741ab68efef37cc0423f0f5a5a636d99f7b7ceb3a128692`
- 15m: `8640` lignes, checksum `270fde3b7202506c5130813310b8f8b27e8e067090f37695b9ef278766257b73`
- 1h: `2160` lignes, checksum `d728ec27b782c38936b6f5dbaeab03ce3c1ceed07e87cc9d750784d2fa3b7b1b`

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
