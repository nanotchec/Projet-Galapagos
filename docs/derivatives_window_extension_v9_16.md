# V9.16 - Derivatives Window Extension Diagnostic

## Resume executif
- Decision V9.16 : `data_extension_should_collect_more_history`.
- Justification : Funding a une couverture locale post-V9 mais ne recouvre pas les aggTrades; open interest est trop court. Il faut collecter/valider l'historique manquant avant toute feature candidate.
- Recommandation suivante : V9.17 - Derivatives History Collection Plan.
- V9.16 est uniquement un diagnostic de fenetre et de disponibilite locale.
- Aucun feature store full, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.

## Inventaire des fenetres
- OHLCV : `2023-03-25T00:00:00Z` -> `2026-05-23T23:59:59Z`.
- aggTrades : `2023-03-25T00:00:00Z` -> `2024-03-24T23:59:59Z`.
- Funding : `2024-05-05 16:00:00+00:00` -> `2026-05-05 08:00:00+00:00`.
- Open interest : `2026-04-02 08:00:00+00:00` -> `2026-05-05 12:00:00+00:00`.
- Autres derivatives : `2026-04-05 12:00:00+00:00` -> `2026-05-05 15:14:11+00:00`.

## Fenetres candidates
- Funding-only + OHLCV/trades : `not_viable`, duree `0` jours.
- Funding + OI + OHLCV/trades : `not_viable`, duree `0` jours.
- Derivatives 4h native : `too_short`, duree `31` jours.
- Multi-year OHLCV/trades sans derivatives : `not_viable`.

## Compatibilite research
- Suffisant pour futur ML : `False`.
- Suffisant pour futur walk-forward : `False`.
- Funding-only plus realiste que OI+funding : `True`.
- Open interest trop court : `True`.

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
- Aucun reseau et aucun telechargement de nouvelles donnees.
- Aucun sidecar et aucune empreinte ZIP.
