# Resultats de commandes V9.27

- `git branch --show-current` : `PASS` (code `0`).
- `git status --short --branch` : `PASS` (code `0`).
- `df -h /Users/lilianserre/Documents/projets/projet-galapagos` : `PASS` (code `0`).
- `df -h /Users/lilianserre/Documents/projets/projet-galapagos/data || true` : `PASS` (code `0`).
- `df -g /Users/lilianserre/Documents/projets/projet-galapagos` : `PASS` (code `0`).
- `df -g /Users/lilianserre/Documents/projets/projet-galapagos/data || true` : `PASS` (code `0`).
- `diskutil info /Users/lilianserre/Documents/projets/projet-galapagos || true` : `PASS` (code `1`).
- `diskutil apfs list || true` : `PASS` (code `0`).
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/raw 2>/dev/null || true` : `PASS` (code `0`).
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/silver 2>/dev/null || true` : `PASS` (code `0`).
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/quarantine 2>/dev/null || true` : `PASS` (code `0`).
- `python - <<PY
import os, json; print(os.statvfs(project)); print(os.statvfs(data))
PY` : `PASS` (code `0`).
- `python -m py_compile src/galapagos/data/aggtrades_post_v9_storage_recheck_resume_v9_27.py src/galapagos/data/aggtrades_post_v9_storage_recheck_resume_v9_27_validation.py scripts/audit_audit_lite_zip_v9_27.py scripts/smoke_audit_lite_zip_v9_27.py` : `PASS` (code `0`).
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` (code `0`).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_storage_recheck_resume_v9_27.py` : `PASS` (code `0`).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_storage_recheck_resume_v9_27_validator.py` : `PASS` (code `0`).
- `python scripts/run_aggtrades_post_v9_storage_recheck_resume_v9_27.py` : `PASS` (code `0`).
- `python - <<PY
# reclassify V9.27 stop reason from generic batch failure to strict quality failure after inspecting batch06 day_results
PY` : `PASS` (code `0`).
- `python scripts/validate_aggtrades_post_v9_storage_recheck_resume_v9_27.py` : `PASS` (code `0`).
- `python scripts/release_audit_lite_zip_v9_27.py` : `PASS` (code `0`).
- `python scripts/audit_audit_lite_zip_v9_27.py --zip projet-galapagos-v9.27-audit-lite.zip` : `PASS` (code `0`).
- `python scripts/smoke_audit_lite_zip_v9_27.py --zip projet-galapagos-v9.27-audit-lite.zip` : `PASS` (code `0`).

- Reseau utilise : `true` (`public_archive_read_only`).
- Telechargement execute : `true`.
- Ingestion executee : `true`.
- Arret : echec qualite strict sur `2026-02-11`.
