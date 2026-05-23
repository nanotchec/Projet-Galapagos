# Latest Summary V4.6

V4.5 est la dernière version validée par audit externe via audit-lite et attestation full locale.

V4.6 est la candidate courante. Elle entraîne uniquement des baselines ML offline simples sur le dataset supervisé 1 an V4.5 validé.

Fenêtre V4.6 : du `2024-01-01` au `2024-12-31` inclus. La cible unique est `up_down_flat_h1` et les modèles autorisés sont `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.

Les fichiers de scores V4.6 produits contiennent `research_predicted_class`, `research_probability_down`, `research_probability_flat` et `research_probability_up`. Row counts scores : `1m=2108036`, `5m=421508`, `15m=140420`, `1h=35012`.

Les métriques V4.6 sont descriptives et non actionnables. Aucun PnL, Sharpe, drawdown, equity curve, profit factor, backtest, stratégie, signal de trading, ordre ou modèle persistant n'est produit.

V4.6 reste `pending_external_audit`.
