# Research Decision Gate V5.6

V5.6 est une porte de decision research apres la chaine OHLCV-only max historical V5.0 -> V5.5.

Verdict : **mitige et non concluant**. Les resultats V5.4/V5.5 montrent un interet descriptif faible, surtout pour `logistic_regression` sur `5m` et `15m`, mais les signaux ne sont pas assez stables entre timeframes et groupes walk-forward pour soutenir une conclusion robuste.

Decision principale : **ajouter les trades publics historiques**.

Decision secondaire : **preparer une validation walk-forward offline plus stricte**.

Roadmap proposee :

- V6.0 : decouverte et ingestion data-only des trades publics historiques BTCUSDT.
- V6.1 : qualite et agregations causales des trades publics.
- V6.2 : assemblage offline OHLCV + trades publics.
- V6.3 : baselines ML offline et falsification sur dataset OHLCV + trades.
- V6.4 : decision gate walk-forward offline plus stricte.

Interdits maintenus :

- pas de trading ;
- pas de paper live ;
- pas d'ordre ;
- pas de backtest validant une strategie ;
- pas de claim de rentabilite ;
- pas de modele valide pour trading.

Voir le rapport complet : `reports/research_decisions/v5_6_research_decision_gate.md`.
