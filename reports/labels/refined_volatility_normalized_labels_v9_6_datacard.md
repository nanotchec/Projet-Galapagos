# V9.6 - Label factory candidate volatility-normalized

V9.6 produit des labels candidats strictement offline et causaux pour la recherche.
Aucun ML, walk-forward, backtest, strategie, signal actionnable, ordre, paper live ou trading reel n'est produit.

## Decision

- Decision : `label_factory_candidate_created_volatility_normalized`.
- Multiplicateur selectionne : `0.5`.

## Distributions principales

- `1m` : majoritaire `FLAT` a `0.4680`, entropie `1.5290`, invalides `60`.
  - distribution : `{'DOWN': {'count': 139523, 'rate': 0.26475957341834605}, 'FLAT': {'count': 246639, 'rate': 0.4680234544005465}, 'UP': {'count': 140818, 'rate': 0.26721697218110746}}`.
  - reduction FLAT vs label fixe h1 : `0.3005`.
- `5m` : majoritaire `FLAT` a `0.4342`, entropie `1.5532`, invalides `60`.
  - distribution : `{'DOWN': {'count': 29411, 'rate': 0.27917948133804155}, 'FLAT': {'count': 45739, 'rate': 0.43417055852982495}, 'UP': {'count': 30198, 'rate': 0.2866499601321335}}`.
  - reduction FLAT vs label fixe h1 : `0.0415`.
- `15m` : majoritaire `FLAT` a `0.4419`, entropie `1.5483`, invalides `60`.
  - distribution : `{'DOWN': {'count': 9674, 'rate': 0.27580111757326947}, 'FLAT': {'count': 15499, 'rate': 0.44186908427414756}, 'UP': {'count': 9903, 'rate': 0.28232979815258297}}`.
  - reduction FLAT vs label fixe h1 : `-0.1461`.
- `1h` : majoritaire `FLAT` a `0.4999`, entropie `1.4996`, invalides `60`.
  - distribution : `{'DOWN': {'count': 2098, 'rate': 0.24048601558917929}, 'FLAT': {'count': 4361, 'rate': 0.49988537368179736}, 'UP': {'count': 2265, 'rate': 0.2596286107290234}}`.
  - reduction FLAT vs label fixe h1 : `-0.3370`.

## Interdits maintenus

- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun paper live.
- Aucun trading reel.
- Aucune API privee et aucune cle API.
