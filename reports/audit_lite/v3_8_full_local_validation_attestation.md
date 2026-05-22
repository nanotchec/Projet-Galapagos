# Attestation full locale V3.8

- Version : `V3.8`
- Scope : `full_local`
- Tests passes : `True`
- Validateur passe : `True`
- Audit-lite passe : `True`
- Smoke audit-lite passe : `True`
- Manifest sha256 : `fc907483191427469c6724fedbdcbcc057d08cae51c6662308897b9985c4140a`
- Report sha256 : `fc907483191427469c6724fedbdcbcc057d08cae51c6662308897b9985c4140a`
- Data card sha256 : `ddf2ad3b38d9d4f89807cab3be7b62cba3f88206e5a18ac268dc549194e020ef`

## Commandes

- `python scripts/run_expanded_offline_supervised_dataset_v3_8.py` : rc `0`, 6.081s
- `python scripts/validate_expanded_offline_supervised_dataset_v3_8.py` : rc `0`, 2.594s
- `python -m pytest -q tests/datasets/test_expanded_offline_supervised_dataset_v3_8.py` : rc `0`, 0.691s
- `python -m pytest -q tests/validation/test_expanded_offline_supervised_dataset_v3_8_validator.py` : rc `0`, 4.809s
- `python scripts/release_audit_lite_zip_v3_8.py` : rc `0`, 0.924s
- `python scripts/audit_audit_lite_zip_v3_8.py --zip projet-galapagos-v3.8-audit-lite.zip` : rc `0`, 0.403s
- `python scripts/smoke_audit_lite_zip_v3_8.py --zip projet-galapagos-v3.8-audit-lite.zip` : rc `0`, 0.389s
- `python -m pytest --collect-only -q` : rc `0`, 2.147s

## Datasets full

- `1m` dataset : `59f92e9e88e2a3ead2f69a46564dbbef7395bf9f49dd5a78f83333f630ba8c8f` (129600 lignes, 50430089 octets)
- `5m` dataset : `4cc18c1d9294c625fd096139fe5015a8ce8670099f9f5fa2d514463630925ffb` (25920 lignes, 10234779 octets)
- `15m` dataset : `777f3a90ce66df96adc4f32a12073d100ea0ae7ee18d1bd84302ce528dd1b667` (8640 lignes, 3474031 octets)
- `1h` dataset : `c2a8a08f05606b338119e0ab4f6e3c2e27462e859ada2d37d4ecd48b9d3e644f` (2160 lignes, 890090 octets)

## Splits full

- `1m` splits : `5e5d01051da6014e48f46fbc1448cd19f44532bd49ed3f9b31d4776e9fe774d5` (129600 lignes, 5543302 octets)
- `5m` splits : `630658cddfb0978d07a5b0ed24172378192a668d8493634e415c0ca8b76b89d8` (25920 lignes, 1085413 octets)
- `15m` splits : `b16d7cac8d1fd260a4b14f4aca24d07802015e1180c5868d09bf3b348c8f2908` (8640 lignes, 369543 octets)
- `1h` splits : `98211c47a2f5767429e246ad23812fa342a31b37e01b59017df3a85e978649d3` (2160 lignes, 94968 octets)

## Securite

- Aucun trading.
- Aucun backtest.
- Aucun ordre.
- Aucun modele ML V3.8.
