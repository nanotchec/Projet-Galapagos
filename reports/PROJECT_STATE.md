# Synthese courante - V9.43

- Derniere version validee : `V9.42`.
- Candidate : `V9.43`.
- Statut : `pending_external_audit`.
- Direction : `ohlcv_aggtrades_5y_offline_ml`.
- Decision V9.43 : `offline_ml_5y_completed_but_close_to_shuffled_labels`.
- Target : `up_down_flat_volnorm_h1_5y`.
- Features : `41`.
- Modeles : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Resultat : proche des labels melanges et faible vs baselines, donc pas de passage automatique en walk-forward.
- Recommandation : V9.44 - 5Y ML Diagnostic / Feature Review.
- ML offline execute sans modele persistant.
- Aucun trading, paper live, ordre, walk-forward, backtest, strategie ou signal actionnable.
- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.
