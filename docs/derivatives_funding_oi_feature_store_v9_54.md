# V9.54 - Funding / OI Feature Store Candidate

V9.54 n'a pas ete execute dans le run groupe V9.52_to_V9.55.

Raison : V9.53 s'est arrete sur une source issue controlee. Le ZIP mensuel public `BTCUSDT-fundingRate-2026-05.zip` n'etait pas disponible sur `data.binance.vision`, et le fallback REST public limite a la queue 2026-05-01 -> 2026-05-05 a retourne `HTTP 451` dans cet environnement.

Aucun feature store derivatives n'a donc ete cree. Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal n'a ete produit.
