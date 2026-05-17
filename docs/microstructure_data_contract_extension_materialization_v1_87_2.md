# Microstructure Data Contract Extension Materialization V1.87.2

## Overview
This document describes the V1.87.2 extension of the micro-matérialisation.
It focuses on strict validation of release artifacts and documentation.

## Validation logic
The `validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py` script:
1. Verifies existence of all 13 mandatory files (reports, docs, metrics).
2. Checks cross-file alignment for 47 critical fields.
3. Enforces strict safety invariants (no network, no ML, no trading).
4. Performs physical check of V1.87 output directory (exactly 2 files).
5. Validates SHA-256 hashes for all V1.84 data files.
6. Ensures smoke test passed and zip audit is successful.

## Artifacts Checked
- `extension_manifest.json`
- `extension_quality_summary.json`
- `v1_84/manifest.json` (hash 524c...)
- `v1_84/schema_snapshot.json` (hash 2ef9...)
- `v1_84/preview_records.json` (hash 2ec5...)
