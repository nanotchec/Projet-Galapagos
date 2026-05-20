# Multi-Day Public Market Data V2.9

## Correction V2.9.1

V2.9.1 finalise le runtime des tests du validateur V2.9.

V2.9 a été refusée en strict uniquement parce que le fichier complet `tests/validation/test_multi_day_public_market_data_v2_9_validator.py` était trop lent. V2.9.1 conserve les mêmes artefacts data et le même validateur de production, mais remplace les tests non physiques par des appels ciblés aux helpers de validation.

V2.9.1 reste `pending_external_audit`.

## Objectif

V2.9 construit une preview multi-day de données marché publiques réelles, bornée et validée physiquement.

La fenêtre est fixe :

- source : Binance public archive ;
- market type : spot ;
- symbole : BTCUSDT ;
- timeframe source : 1m ;
- dates : 2024-01-15 à 2024-01-21 inclus ;
- durée : 7 jours.

## Sorties

Les sorties V2.9 sont séparées des artefacts validés V2.3 à V2.8.4 :

`data/research/v2_9/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=<tf>/window=2024-01-15_2024-01-21/ohlcv.parquet`

Row counts attendus :

- 1m : 10080 ;
- 5m : 2016 ;
- 15m : 672 ;
- 1h : 168.

## Validation

Le validateur V2.9 recalcule physiquement :

- existence et checksums des 7 raw zips ;
- row counts raw par jour ;
- existence, checksums, bytes et row counts des outputs ;
- schéma strict `OHLCV_COLUMNS` ;
- timestamps UTC ;
- monotonie physique ;
- trous et doublons ;
- invariants OHLC ;
- volumes négatifs ;
- cohérence raw -> 1m ;
- cohérence parent-child 1m -> 5m / 15m / 1h ;
- projection déterministe du rapport JSON depuis le manifest ;
- Markdown sans claim interdite ;
- flags de sécurité.

## Limites

V2.9 ne produit aucune feature.
V2.9 ne produit aucun label.
V2.9 ne produit aucun dataset ML.
V2.9 ne produit aucun modèle ML.
V2.9 ne produit aucun backtest.
V2.9 ne produit aucune stratégie.
V2.9 ne produit aucun signal de trading.
V2.9 ne produit aucun ordre.
V2.9 n'autorise aucun paper live.
V2.9 n'autorise aucun trading réel.

V2.9 reste `pending_external_audit` avant validation externe.
