# Attestation full locale V4.4

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_one_year_label_factory_v4_4.py` : PASS, 14.85s
- `python scripts/validate_one_year_label_factory_v4_4.py` : PASS, 11.55s
- `python -m pytest -q tests/labels/test_one_year_forward_labels_v4_4.py` : PASS, 1.01s
- `python -m pytest -q tests/validation/test_one_year_label_factory_v4_4_validator.py` : PASS, 13.1s
- `python scripts/release_audit_lite_zip_v4_4.py` : PASS, 0.97s
- `python scripts/audit_audit_lite_zip_v4_4.py --zip projet-galapagos-v4.4-audit-lite.zip` : PASS, 0.32s
- `python scripts/smoke_audit_lite_zip_v4_4.py --zip projet-galapagos-v4.4-audit-lite.zip` : PASS, 0.59s
- `python -m pytest --collect-only -q` : PASS, 2.21s

## Outputs labels complets

- `15m` : `35136` lignes, checksum `14904660ce5eb37b303c749919f80b0ecb794268f0648975d33fdaddd93cda9c`
- `1h` : `8784` lignes, checksum `f53f0780594ad648bb99b804e5e76ce418466a65c1689d26401c1d8ef492cecd`
- `1m` : `527040` lignes, checksum `1a5f2ad160ce7245a5bb38404fee717ad535d913786264d9622002390f71a9e0`
- `5m` : `105408` lignes, checksum `174740f0c2cddb11ba5cc574cf2565da77ffb4fc1d5996612d133f613ec43058`
