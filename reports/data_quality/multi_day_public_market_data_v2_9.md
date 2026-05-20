# Multi-Day Public Market Data V2.9

## Objectif

V2.9 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 7 jours, du 2024-01-15 au 2024-01-21.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2024-01-15` -> `2024-01-21`
- Run : `v2_9_20260520T213632Z_86e3ed9f`

## Fichiers raw

- 2024-01-15: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip`, checksum `281154f7aab59486732bbe9ad19e8ad9cbaeb7142565cce4b3edf6406301ebf8`
- 2024-01-16: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-16.zip`, checksum `96d8c3e7f66bd8f94d888fac3b078e2223aceec6b3898a2395a240e0eb7d0399`
- 2024-01-17: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-17.zip`, checksum `91790216ea49ea61b27f3b8382ce76a405d63cc2c40a0b29591cb4cc346de11d`
- 2024-01-18: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-18.zip`, checksum `1c6715e192a6de81269303ce4fadaa2deec57373691834a721e2dfa9e2c65efc`
- 2024-01-19: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-19.zip`, checksum `62aa2b0434e7bbb8cf77731b9916c35194867c9fad946f57a29b8e301abd33c9`
- 2024-01-20: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-20.zip`, checksum `8c0e45887e167f7f15319257a2b97f3b66044f4bd9c8939fcaf7141e8c088159`
- 2024-01-21: `1440` lignes, `data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-21.zip`, checksum `2784cf791667a6f985919902e3108b55be542d506187f4289a7026eaa2d8e62a`

## Outputs

- 1m: `10080` lignes, checksum `706e45ebe15cd22c00652171d68386368b2dc67522529495712a9d4f37d3c5d4`
- 5m: `2016` lignes, checksum `b2655d8181b1ae9776def91a0b4330fba1300d1d416d45868e393706926ad92c`
- 15m: `672` lignes, checksum `8670e94fce6b994499cacea0db70fea11b3844894d04ce8ca74501ed3765e491`
- 1h: `168` lignes, checksum `b523e6b504df08b23b11db267dd4406c4a80747c3342d009c0b1bcb724b766e6`

## Qualite

- 1m: gaps `0`, doublons `0`, parent-child `True`
- 5m: gaps `0`, doublons `0`, parent-child `True`
- 15m: gaps `0`, doublons `0`, parent-child `True`
- 1h: gaps `0`, doublons `0`, parent-child `True`

## Limitations

- V2.9 etend uniquement les donnees marche publiques BTCUSDT sur une fenetre fixe de 7 jours.
- V2.9 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V2.9 ne valide aucune strategie.
V2.9 ne produit aucune feature.
V2.9 ne produit aucun label.
V2.9 ne produit aucun dataset ML.
V2.9 ne produit aucun modele ML.
V2.9 ne produit aucun backtest.
V2.9 ne produit aucun signal de trading.
V2.9 ne produit aucun ordre.
V2.9 n'autorise aucun paper live.
V2.9 n'autorise aucun trading reel.
