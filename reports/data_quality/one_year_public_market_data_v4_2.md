# One-Year Public Market Data V4.2

## Objectif

V4.2 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 1 an, du 2024-01-01 au 2024-12-31. La fenetre couvre 366 jours car 2024 est bissextile.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `2024-01-01` -> `2024-12-31`
- Run : `v4_2_20260522T214610Z_f92fad4e`

## Outputs

- 1m: `527040` lignes, checksum `9ca673ee5b8f8e496ac76defddbf5f92924087cb9a7d8c11d33753edf052e156`
- 5m: `105408` lignes, checksum `91914c5d6b7e475d36145d1156c5a3d07fa60e7c5de26d3ce432551d1fff3091`
- 15m: `35136` lignes, checksum `92d2eaa6d75b08be0f13cc2b3fd5f1b73a36ba394f5fae16fa5906e37907fdef`
- 1h: `8784` lignes, checksum `cc2ed4e04ce9efc499831d55584b948a2dd990443d3be9614de27c3a671fd4e0`

## Qualite

- 1m: gaps `0`, doublons `0`, parent-child `True`
- 5m: gaps `0`, doublons `0`, parent-child `True`
- 15m: gaps `0`, doublons `0`, parent-child `True`
- 1h: gaps `0`, doublons `0`, parent-child `True`

## Limitations

- V4.2 etend uniquement les donnees marche publiques BTCUSDT sur une fenetre fixe de 1 an.
- V4.2 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V4.2 ne valide aucune strategie.
V4.2 ne produit aucune feature.
V4.2 ne produit aucun label.
V4.2 ne produit aucun dataset ML.
V4.2 ne produit aucun modele ML.
V4.2 ne produit aucun backtest.
V4.2 ne produit aucun signal de trading.
V4.2 ne produit aucun ordre.
V4.2 n'autorise aucun paper live.
V4.2 n'autorise aucun trading reel.
