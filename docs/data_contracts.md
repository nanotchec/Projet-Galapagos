# Contrats de donnees

## MarketSnapshot

Champs principaux : `timestamp_utc`, `profile`, `asset`, `timeframe`, `market`, `indicators`,
`derivatives`, `scenarios`, `data_quality`.

## Decision agent

Schema strict Pydantic `AgentDecision`. Decisions autorisees : `LONG`, `SHORT`, `CLOSE`, `HOLD`,
`NO_TRADE`. Strategies autorisees : `no_trade`, `breakout`, `momentum`, `mean_reversion`,
`derivatives_signal`, `volatility_regime`, `risk_reduction`, `close_position`.

## Trade paper

Champs : timestamps entree/sortie, side, prix entree/sortie, stop_loss, take_profit, taille, frais,
slippage, PnL, strategie, profil, statut, raison de cloture.

## Positions ouvertes

Les positions ouvertes sont stockees dans `positions` sous forme JSON issue du dataclass `Position`.
Elles sont rechargees avant chaque cycle puis remplacees apres evaluation des sorties et execution
paper eventuelle.

## Timestamps

Toutes les dates stockees par Galapagos sont en UTC ISO 8601.
