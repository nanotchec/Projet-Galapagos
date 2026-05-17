# Code Review V1.81.7

## Scope

Galapagos V1.81.7 – correctif de V1.81.6.

**Mission** : `fix_cli_contract_src_imports_required_research_reports_report_index_and_smoke_without_pythonpath`

## Problèmes Corrigés

1. **CLI `--approval-phrase` absent** → Ajout de l'argument dans `run_*_v1_81_7.py`.
2. **Scripts non portables sans PYTHONPATH** → Bootstrap `sys.path` ajouté en tête de tous les scripts.
3. **Rapports écrits à la racine `reports/`** → Rapports déplacés dans `reports/research/` avec noms canoniques.
4. **`docs/code_review_v1_81_6.md` absent** → Créé pour V1.81.7.
5. **REPORT_INDEX non canonique** → Section V1.81.7 avec liens vers `reports/research/`.
6. **Smoke test sans preuve de portabilité** → 3 commandes sans PYTHONPATH injecté.

## Invariants de Sécurité

- Aucun réseau exécuté.
- Aucune écriture dans `data/`.
- Aucun trading réel possible.
- Aucun ordre possible.

## Verdict

`V1_81_7_CLI_IMPORT_REPORTS_AND_SMOKE_HARDENING_PASSED`
