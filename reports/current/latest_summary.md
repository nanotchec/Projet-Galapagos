# Latest Summary V8.1

V8.0 est la derniere version validee par audit externe.

V8.1 est la candidate courante. Elle produit uniquement un decision gate research apres la chaine OHLCV + aggTrades 90 jours.

Fenetre analysee : `2023-03-25` -> `2023-06-22`.

Total jours : `90`.

Feature columns count V8.0 : `71`.

Verdict : OHLCV + aggTrades 90 jours est interessant mais mitige et non concluant. Les modeles battent souvent les baselines descriptives, mais les alertes label shuffle et la concentration par timeframe empechent de recommander un backtest.

Recommendation principale : A. Etendre les aggTrades a 1 an.

Recommendation secondaire : D. Preparer une validation walk-forward offline plus stricte.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.
