# Public Trades Historical Ingestion Preview V7.0

## Objectif

V7.0 ingere uniquement des trades publics historiques Binance `aggTrades` pour `BTCUSDT` spot.

## Fenetre

- Fenetre : `2023-03-25` -> `2023-03-25`.
- Total jours : `1`.
- Meme fenetre que V5.0 : `False`.
- Raison : bounded V7.0 preview window selected because full V5.0 aggTrades history is too large for the first auditable ingestion layer.

## Raw inventory

- `2023-03-25` : `817141` lignes, `11729875` octets, checksum `5bba0a4fa33fb258d19fb6e8ab414f15ae15dc5ecb5f3a2a2e0c31a403193a85`

## Output

- Path : `data/research/v7_0/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-03-25/agg_trades.parquet`.
- Rows : `817141`.
- SHA256 : `ceb1577c8b1a26da39edcd44eae9499158405e6f16fc10e91dc3613819654e65`.

## Qualite

- Doublons `aggregate_trade_id` : `0`.
- IDs non monotones : `0`.
- Timestamps non monotones : `0`.
- Prix non positifs : `0`.
- Quantites non positives : `0`.
- Colonnes interdites : `[]`.

## Limitations

- V7.0 ingere uniquement des trades publics historiques en lecture seule.
- V7.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V7.0 ne valide aucune strategie.
V7.0 ne produit aucune feature.
V7.0 ne produit aucun label.
V7.0 ne produit aucun dataset ML.
V7.0 ne produit aucun modele ML.
V7.0 ne produit aucun backtest.
V7.0 ne produit aucun signal de trading.
V7.0 ne produit aucun ordre.
V7.0 n'autorise aucun paper live.
V7.0 n'autorise aucun trading reel.
