# Resultats commandes V9.24

- Statut global : `PASS`.
- Decision : `aggtrades_post_v9_batch3_collection_success`.
- Batch : `2024-10-09` -> `2024-12-07`.
- Jours telecharges/normalises/valides : `60` / `60` / `60`.
- Lignes/raw/silver : `124227690` / `1553341925` / `3004532928`.
- Audit ZIP : `True`.
- Smoke ZIP : `True`.

## Commandes
- `git branch --show-current` : `PASS` - main
- `git status --short --branch` : `PASS` - ## main...origin/main [ahead 5]
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` - 5515 tests collected in 2.02s
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_batch3_collection_v9_24.py` : `PASS` - 13 passed in 0.53s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_batch3_collection_v9_24_validator.py` : `PASS` - 9 passed in 0.05s
- `python scripts/run_aggtrades_post_v9_batch3_collection_v9_24.py --mode collect --start-date 2024-10-09 --end-date 2024-12-07 --max-downloads 60` : `PASS` - 60 downloaded, 60 normalized, 60 complete, 0 failed
- `python scripts/validate_aggtrades_post_v9_batch3_collection_v9_24.py` : `PASS` - passed=true, errors=[]
- `python scripts/release_audit_lite_zip_v9_24.py` : `PASS` - ZIP PASS
- `python scripts/audit_audit_lite_zip_v9_24.py --zip projet-galapagos-v9.24-audit-lite.zip` : `PASS` - passed=true, errors=[]
- `python scripts/smoke_audit_lite_zip_v9_24.py --zip projet-galapagos-v9.24-audit-lite.zip` : `PASS` - passed=true, errors=[]

- Aucun sidecar et aucune empreinte ZIP.
