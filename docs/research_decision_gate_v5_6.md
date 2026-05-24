# Research Decision Gate V5.6

V5.6 est une porte de decision research apres la chaine OHLCV-only max historical V5.0 -> V5.5.

Correction V5.6.1 : la decision de roadmap est corrigee. Les trades publics historiques ne sont plus la prochaine etape immediate ; ils sont repousses a V7.x apres validation ou rejet de la piste Advanced OHLCV.

Verdict : **mitige et non concluant**. Les resultats V5.4/V5.5 montrent un interet descriptif faible, surtout pour `logistic_regression` sur `5m` et `15m`, mais les signaux ne sont pas assez stables entre timeframes et groupes walk-forward pour soutenir une conclusion robuste. Les features OHLCV actuelles restent trop simples pour clore la piste OHLCV-only.

Decision principale : **ameliorer les features OHLCV avant multi-source**.

Decision secondaire : **preparer une validation walk-forward offline plus stricte**.

Roadmap proposee :

- V6.0 : Max Historical Advanced OHLCV Feature Expansion.
- V6.1 : Max Historical Dataset with Advanced OHLCV Features.
- V6.2 : Max Historical Offline ML with Advanced OHLCV Features.
- V6.3 : Advanced OHLCV Robustness / Walk-Forward Falsification.
- V6.4 : Advanced OHLCV Research Decision Gate.

Les trades publics historiques sont repoussés à V7.x après validation ou rejet de la piste Advanced OHLCV.

Interdits maintenus :

- pas de trading ;
- pas de paper live ;
- pas d'ordre ;
- pas de backtest validant une strategie ;
- pas de claim de rentabilite ;
- pas de modele valide pour trading.

V5.6 ne valide aucune strategie, ne valide aucun modele exploitable en trading, ne produit aucun backtest, ne produit aucun signal et ne produit aucun ordre.

Voir le rapport complet : `reports/research_decisions/v5_6_research_decision_gate.md`.
