# Projet Galapagos

- Derniere version validee : V8.7.
- Candidate : V8.8, strict walk-forward research decision gate.

V8.8 analyse la validation walk-forward offline stricte V8.7 et produit une decision research sans modifier les donnees, les features, les labels, les datasets ou les scores.

Fenetre : `2023-03-25` -> `2024-03-24`, `366` jours.

Feature columns : `71`.

Verdict : `interessant_mais_instable_non_concluant`.

Recommandation principale : A. Ameliorer/refactoriser les features OHLCV + trades.

Recommandation secondaire : B. Revoir les labels.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.8

```bash
python scripts/run_research_decision_gate_v8_8.py
python scripts/validate_research_decision_gate_v8_8.py
python -m pytest -q tests/validation/test_research_decision_gate_v8_8.py
python -m pytest --collect-only -q
```
