# Projet Galapagos

- Derniere version validee : V8.0.
- Candidate : V8.1, OHLCV + public trades 90-day research decision gate.

V8.1 analyse les resultats V8.0 ML offline et robustesse/falsification sur le dataset V7.9 OHLCV + aggTrades 90 jours. Le verdict est research-only : les resultats sont interessants mais mitigés et non concluants.

Fenetre : `2023-03-25` -> `2023-06-22`, `90` jours.

Feature columns ML V8.0 : `71`.

Recommendation principale V8.1 : etendre les aggTrades a 1 an. Recommendation secondaire : preparer une validation walk-forward offline plus stricte.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.1

```bash
python scripts/validate_research_decision_gate_v8_1.py
python -m pytest -q tests/validation/test_research_decision_gate_v8_1.py
python -m pytest --collect-only -q
```

V8.1 ne valide aucune strategie, aucun modele exploitable en trading et aucune rentabilite.
