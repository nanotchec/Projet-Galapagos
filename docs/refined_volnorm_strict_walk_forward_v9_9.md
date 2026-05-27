# V9.9 - Strict walk-forward avec labels volatility-normalized

V9.9 est une validation offline stricte. Ce n'est pas un backtest et ne produit aucun signal actionnable.

- Decision : `strict_walk_forward_completed_but_close_to_shuffled_labels`.
- Cible : `up_down_flat_volnorm_h1`.
- `1m` : `5` folds.
- `5m` : `5` folds.
- `15m` : `5` folds.
- `1h` : `5` folds.

## Interdits maintenus

- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun modele persistant.
- Aucun trading reel.
