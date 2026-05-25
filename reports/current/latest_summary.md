# Latest Summary V8.5

V8.4 est la derniere version validee par audit externe.

V8.5 est la candidate courante. Elle entraine uniquement des baselines ML offline simples sur le dataset V8.4 avec OHLCV + public trades features, produit des scores de recherche `research_*`, calcule des metriques descriptives par split et par groupe walk-forward, et compare descriptivement V8.5 a V8.0/V7.4/V6.2/V5.4 si disponible.

Fenetre utilisee : `2023-03-25` -> `2024-03-24`.

Total jours : `366`.

Row counts scores : `{'1m': 2107920, '5m': 421392, '15m': 140304, '1h': 34896}`.

Feature columns ML : `71`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.5 reste `pending_external_audit`.
