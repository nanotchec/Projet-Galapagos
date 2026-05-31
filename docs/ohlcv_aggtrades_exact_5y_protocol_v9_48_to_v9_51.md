# V9.48 a V9.51 - Protocole OHLCV + AggTrades exact 5Y

- Decision globale : `combined_features_chain_completed_but_no_walk_forward_recommended`.
- Decision V9.51 : `combined_features_5y_ml_completed_but_class_collapse`.
- Clear wins vs baselines : `0`.
- No-clear vs shuffled labels : `10`.
- Class collapse warnings : `12`.
- Mean macro-F1 delta vs V9.43 : `0.007206544444404546`.

Conclusion : les features exactes aggTrades ne justifient pas une future walk-forward immediate dans cet etat. La suite recommandee est un diagnostic funding/open interest ou redesign label/features.

Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, reseau ou telechargement.
