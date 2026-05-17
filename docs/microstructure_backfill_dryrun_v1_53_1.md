# Microstructure Backfill Dry-Run Specification (V1.53.1)

## Goal
The goal of the V1.53.1 phase is to define a strict theoretical dry-run plan for the collection (backfill) of microstructure data. This plan is fully isolated from external networks and strictly prohibits any downloaded data, ensuring the environment remains in a pristine research state (`INFRASTRUCTURE_ONLY`).

## Source Adapter Contracts
Two data sources are approved for the dry-run:
- **Binance Public Data Archives**: Supports historical bulk downloads (`https://data.binance.vision/data/futures/um/daily/klines/`).
- **Bybit V5 API**: Supports programmatic backfills (`https://api.bybit.com/v5/market/kline`).

*Note: In V1.53.1, network execution for these adapters is explicitly `False`.*

## Backfill Priorities
1. **Priority Period**: Full year 2026 (`2026-01-01` to `2026-12-31`).
2. **Priority Asset**: `BTCUSDT` (1m interval).
3. **Execution Plan**: The scheduler divides the bulk 2026 download into monthly chunks.

## Causal Policy & Artifact Safety
A strict anti-leakage policy is set: `available_ts` MUST strictly precede `decision_ts`. All collected data in the future must emit a structured manifest adhering to the specified schema, tracing the ingest and availability timestamps.

## QC Validation
Once real collection begins (not in V1.53.1), a rigorous post-collection quality control process will execute, checking missingness (<2%), gaps (<5 min), and monotonicity before data is promoted to the `silver` tier.
