# Expanded Public Market Data V3.5

Note V3.5.1 : correction strictement runtime et ZIP completeness. Les donnees OHLCV V3.5 restent identiques ; V3.5.1 rend le ZIP auto-testable et accelere run/validate/smoke/tests sans creer de features, labels, dataset ML, ML, backtest, strategie ou ordre.

## Objectif

V3.5 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 90 jours, du 2024-01-01 au 2024-03-30.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2024-01-01` -> `2024-03-30`
- Run : `v3_5_20260522T080224Z_e1153bd0`

## Outputs

- 1m: `129600` lignes, checksum `8e6d3fd31719fd143ac3bf191b0c5fb5fa0838d1fa914273762eccdd3fec8913`
- 5m: `25920` lignes, checksum `e73217997ea9decba3d173d62c76ce195eeba55e52917fcf85b331fc870d3902`
- 15m: `8640` lignes, checksum `e38895cb4d09cef74d3901608aca6d6867cb6780b77a8c8ef77afe6deee0fccc`
- 1h: `2160` lignes, checksum `61098b1c8127c54bac7347b254abf2c727d9e59a792dec4421c121850b1792e0`

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
