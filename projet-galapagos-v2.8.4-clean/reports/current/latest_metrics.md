# État du Projet : V2.7.2 validée + candidat V2.8.4

- **Dernière version validée** : V2.7.2.
- **Version candidate** : V2.8.4.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : offline ML validator runtime and smoke timeout finalization.
- **Scope** : entraînement ML offline simple déjà produit en V2.8, avec correction V2.8.4 limitée au runtime du test nominal, aux tests de score et au smoke silencieux.
- **Modèles autorisés** : majority class, random seed baseline, logistic regression, decision tree depth 2.
- **Target** : `up_down_flat_h1`.
- **Refus strict V2.8** : scripts release/audit non autonomes et garde-fou insuffisant contre `reports/backtests` et modèles persistants sous `data/gold/ml`.
- **Refus strict V2.8.1** : fichier complet `tests/validation/test_offline_ml_research_v2_8_validator.py` trop lent en audit externe.
- **Refus strict V2.8.2** : tests de mutation score encore trop coûteux et smoke ZIP fragile à cause de la capture du gros JSON ML.
- **Non-usage** : aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre, aucun modèle persistant, aucun paper live, aucun trading réel.
- **Validation externe** : V2.8.4 n'est pas validée avant audit externe.
