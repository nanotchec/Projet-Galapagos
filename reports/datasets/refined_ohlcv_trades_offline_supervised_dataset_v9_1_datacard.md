# Data Card V9.1 - Dataset supervise raffine OHLCV + trades

## Usage

Ce dataset est reserve a la recherche offline. Il contient des labels forward uniquement parce qu'il s'agit d'un assemblage supervise hors ligne.

## Sources

- Features raffinees : `reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json`.
- Labels : `reports/manifests/max_history_label_factory_v5_2_manifest.json`.

## Contraintes

- Aucun usage trading n'est autorise par V9.1.
- Les splits sont temporels et sans shuffle.
- Les features sources ne sont pas modifiees.
- Les labels sources ne sont pas modifies.

## Limites

- V9.1 assemble uniquement un dataset supervise offline a partir des features raffinees V9.0 et labels V5.2.
- V9.1 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.
