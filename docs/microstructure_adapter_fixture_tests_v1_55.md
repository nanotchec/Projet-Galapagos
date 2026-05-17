# Microstructure Adapter Fixture Tests (V1.55)

## Overview
This document specifies the refinement of microstructure source adapters (Binance/Bybit) and the local fixture testing infrastructure implemented in V1.55.

## Methodology
To validate the collector architecture without network access, we use local synthetic fixtures.

### Components
1. **FixtureLoader**: Securely loads JSON files from `tests/fixtures/microstructure/`.
2. **FieldMapper**: Normalizes raw exchange data into a standard schema.
3. **TimestampNormalizer**: Ensures causal consistency (`event_ts <= available_ts <= ingest_ts`).
4. **NormalizedRecordSchema**: Pydantic model for data integrity.

### Mapped Fields
- **Binance**: Full OHLCV + Taker buy volumes + Trade count.
- **Bybit**: OHLCV + Quote volume (Taker volumes missing in minimal stub).

## Safety Guards
- **Network Disabled**: Strict monkey-patching of sockets.
- **Local Fixture Only**: No external API calls.
- **No Data Writes**: No parquet/csv/db files created.
- **Path Guard**: `FixtureLoader` rejects any path outside the allowed test directory.

## Verdict
**MICROSTRUCTURE_ADAPTER_FIXTURE_TESTS_READY**

## Next Steps
Implement collector contract approval checks to ensure all requirements are met before allowing any controlled collection.
