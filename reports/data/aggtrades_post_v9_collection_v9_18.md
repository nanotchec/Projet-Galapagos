# V9.18 - AggTrades Post-V9 Collection Pack

## Resume executif
- Mode execute : `dry-run`.
- Decision V9.18 : `aggtrades_post_v9_collection_pack_ready_dry_run_only`.
- Justification : Le pack de collecte est pret et le dry-run inventorie la fenetre cible sans executer de reseau.
- Recommandation suivante : V9.19 - AggTrades Post-V9 Collection Execution.
- V9.18 reste data-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.

## Source publique ciblee
- Source : `Binance public archive aggTrades daily files`.
- Host : `data.binance.vision`.
- Marche : `spot`.
- Symbole : `BTCUSDT`.
- Compte requis : `False`.
- Cle API requise : `False`.
- Endpoint prive requis : `False`.
- Websocket live requis : `False`.

## Fenetre cible
- Fenetre de collecte : `2024-03-25` -> `2026-05-05`.
- Jours attendus : `772`.
- Jours deja presents : `0`.
- Jours manquants : `772`.
- Couverture : `0.0`.

## Convention de stockage
- Bronze/raw : `data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-{date}.zip`.
- Silver normalise : `data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date={date}/agg_trades.parquet`.

## Qualite et causalite
- Checks par jour : presence, lisibilite, schema, types, timestamps UTC, prix/quantite positifs, doublons, coherence date partition, taille non nulle.
- Checks fenetre : jours attendus, jours presents, gaps, doublons, min/max timestamp, min/max aggregate_trade_id, lignes invalides, quarantine.
- Anti-leakage : `available_ts >= event_ts`, aucune jointure label, aucune integration funding/OI dans V9.18.

## Garde-fous
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest execute.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- Aucun client exchange authentifie.
- Aucun websocket live.
- Aucun sidecar et aucune empreinte ZIP.
- Aucun reseau utilise.
- Aucun telechargement execute.
- Aucune ingestion executee.
