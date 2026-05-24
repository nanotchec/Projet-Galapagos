# Attestation full locale V5.2

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_max_history_label_factory_v5_2.py` : PASS
- `python scripts/validate_max_history_label_factory_v5_2.py` : PASS
- `python -m pytest -q tests/labels/test_max_history_forward_labels_v5_2.py` : PASS
- `python -m pytest -q tests/validation/test_max_history_label_factory_v5_2_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v5_2.py` : PASS
- `python scripts/audit_audit_lite_zip_v5_2.py --zip projet-galapagos-v5.2-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v5_2.py --zip projet-galapagos-v5.2-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs labels complets

- 15m: `110976` lignes, checksum `1a4415aa349c67547d985088fefdf5dcd1dc2f796d1389a71155ba079d2d2666`
- 1h: `27744` lignes, checksum `cfe958a39906f89cdba910ec0d820e5357b751385111c9f0e74e49559b2ceceb`
- 1m: `1664640` lignes, checksum `49b79a14249afc1bd3e543fac7bf6fd1ee0e6cd741f3516af144488d845a12c9`
- 5m: `332928` lignes, checksum `674f7f7b5cd32159d93b897e88d0b8e46bcab2c444e384467d59825e2f96ed04`
