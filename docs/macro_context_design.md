# Design du contexte macro

Ce document decrit une extension future du contexte Galapagos. Elle n'est pas implementee en live
en V1.10.2.

## Objectif

Ajouter un contexte macro explicite sans hallucination et sans melanger donnees indisponibles avec
des signaux reels.

## Variables proposees

- `macro_regime`: `risk_on`, `risk_off`, `neutral`, `unknown`
- `equity_market_trend`
- `dxy_trend`
- `rates_pressure`
- `btc_etf_flow_regime`
- `crypto_liquidity_regime`
- `major_event_risk`
- `macro_confidence`
- `macro_last_updated`

## Regles

- Le modele ne doit jamais inventer de donnees macro.
- Les donnees macro doivent venir d'un module separe et journalise.
- Si `macro_regime=unknown`, le modele doit rester prudent.
- La macro sert de filtre de regime, pas de signal isole.
- Chaque variable doit avoir un statut : `available`, `unavailable`, `error` ou `stale`.

## Sources futures possibles

Les sources exactes ne sont pas branchees en V1.10.2. Elles devront etre choisies plus tard avec
licence, frequence de mise a jour, latence et fiabilite documentees.

## Limite V1.10.2

Aucune API macro live n'est appelee. Ce document prepare seulement l'architecture.
## V1.11 - design readiness macro

Le contexte macro reste `unknown` par defaut en V1.11. Aucun flux macro live
n'est integre dans cette passe.

Variables futures :
- `macro_regime`: `risk_on`, `risk_off`, `neutral`, `unknown`
- `equity_market_trend`
- `dxy_trend`
- `rates_pressure`
- `liquidity_proxy`
- `btc_etf_flow_regime`
- `major_event_risk`
- `macro_confidence`
- `macro_last_updated`

Sources possibles :
- FRED pour taux, proxies DXY/liquidite et macro US.
- Provider dedie pour ETF/fund flows.
- CoinGlass si cle API fournie.

Regles :
- Le modele ne doit jamais inventer la macro.
- Toute donnee macro doit etre horodatee.
- La macro sert de filtre de regime, pas de signal isole.
- Pas de fuite temporelle : seules les donnees disponibles au timestamp de
  decision peuvent entrer dans le contexte.
