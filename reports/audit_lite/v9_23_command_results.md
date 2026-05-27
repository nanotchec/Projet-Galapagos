# Commandes V9.23

- `git branch --show-current && git status --short --branch` : `PASS` (main; ## main...origin/main [ahead 4]).
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` (5493 tests collected in 2.88s).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_batch2_collection_v9_23.py` : `PASS` (12 passed).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_batch2_collection_v9_23_validator.py` : `PASS` (9 passed).
- `python scripts/run_aggtrades_post_v9_batch2_collection_v9_23.py --mode collect --start-date 2024-08-10 --end-date 2024-10-08 --max-downloads 60` : `PASS` (decision=aggtrades_post_v9_batch2_collection_success; days_downloaded=60; days_normalized=60; days_complete=60; rows=73423696; raw_bytes=929788166; silver_bytes=1794798698; runtime_seconds=657.918).
- `python scripts/validate_aggtrades_post_v9_batch2_collection_v9_23.py` : `PASS` (passed=true; errors=[]).
- `python scripts/release_audit_lite_zip_v9_23.py` : `PASS` (included_files=57; sidecars_created=false; zip_fingerprints_created=false).
- `python scripts/audit_audit_lite_zip_v9_23.py --zip projet-galapagos-v9.23-audit-lite.zip` : `PASS` (passed=true; errors=[]).
- `python scripts/smoke_audit_lite_zip_v9_23.py --zip projet-galapagos-v9.23-audit-lite.zip` : `PASS` (passed=true; errors=[]).

- Aucun sidecar SHA256 et aucune empreinte ZIP.
