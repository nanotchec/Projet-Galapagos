# V9.17 - Derivatives History Collection Plan

## Resume executif
- Decision V9.17 : `collection_plan_priority_aggtrades_post_v9_and_funding`.
- Justification : OHLCV already extends beyond funding and funding is local after 2024-05-05; the missing practical blocker is validated aggTrades after 2024-03-24.
- Recommandation suivante : V9.18 - AggTrades Post-V9 Collection Pack.
- V9.17 produit uniquement un plan de collecte historique; aucune collecte n'est executee.
- Aucun feature store full, dataset, ML, walk-forward, backtest, strategie ou signal actionnable.

## Gap actuel
- OHLCV local : `2023-03-25T00:00:00Z` -> `2026-05-23T23:59:59Z`.
- aggTrades valides : `2023-03-25T00:00:00Z` -> `2024-03-24T23:59:59Z`.
- Funding local : `2024-05-05 16:00:00+00:00` -> `2026-05-05 08:00:00+00:00`.
- Open interest local : `2026-04-02 08:00:00+00:00` -> `2026-05-05 12:00:00+00:00`.
- Gap aggTrades vers funding : `42` jours.

## Sources a collecter
- Priorite 1 : aggTrades/public trades post-V9 et funding historique public si disponible.
- Priorite 2 : open interest historique et branche derivatives-native 4h.
- Plus tard : liquidations et long/short ratios uniquement si public no-key et historises proprement.

## Fenetres cibles
- Funding-first post-V9 : `priority_1_collection_plan`.
- V9 historical with added funding : `priority_2_collection_plan`.
- Funding + OI recent : `reject_too_short`.
- Derivatives-native 4h : `priority_2_collection_plan`.

## Plan bronze/silver/research
- Bronze/raw : fichiers publics immuables, sans secret et sans endpoint prive.
- Silver : schemas stricts, timestamps UTC, `event_ts`, `close_ts` si applicable, `source_publish_ts` si applicable, `ingest_ts`, `available_ts`.
- Research : uniquement apres validation de couverture; aucun dataset supervise ni entrainement dans la collecte.

## Interdits maintenus
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
- Aucun reseau, aucun telechargement et aucune ingestion executee.
- Aucun sidecar et aucune empreinte ZIP.
