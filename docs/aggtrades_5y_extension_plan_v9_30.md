# V9.30 - AggTrades 5Y Historical Extension Plan

## Resume
- Decision V9.30 : `aggtrades_5y_extension_plan_ready`.
- Recommandation suivante : `V9.31 - AggTrades 5Y Historical Extension Collection`.
- Fenetre validee actuelle : `2024-05-05` -> `2026-05-05`.
- Fenetre cible 5Y : `2021-05-05` -> `2026-05-05`.
- Fenetre a collecter : `2021-05-05` -> `2024-05-04`.
- Jours deja valides / a collecter : `731` / `1096`.
- Estimation extension raw/silver : `19947096976` / `38796335136` bytes.
- Espace libre data/project : `164.57` / `164.57` GiB.
- Safe pour collecte 5Y : `True`.

## Source
- Source : `Binance public archive aggTrades daily`.
- Host : `data.binance.vision`.
- Disponibilite historique 2021-2024 : probable mais non verifiee par V9.30; confirmation requise en V9.31.

## Plan V9.31
- Lots proposes : `19`.
- Taille max recommandee : `60` jours.
- Premier lot : `2021-05-05` -> `2021-07-03`.
- Dernier lot : `2024-04-19` -> `2024-05-04`.

## Plan V9.32
- Validation globale 2021-05-05 -> 2026-05-05 : raw, silver, jours manquants, doublons, invalid rows, timestamps, partitions, available_ts, quarantines et stabilite schema.

## Limites avant features/ML
- Aucun feature store, dataset, ML, walk-forward, backtest, strategie ou signal avant validation V9.32 puis decision gate.

## Garde-fous
- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.
- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.
- Aucun telechargement de nouvelles donnees, aucune nouvelle ingestion, aucune suppression destructive, aucun push.
- Aucun sidecar et aucune empreinte ZIP.
