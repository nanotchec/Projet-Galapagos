# Source/Rebuild Universe Mismatch Resolution - V1.34.1 (Hardened)

This document summarizes the hardened findings of the V1.34.1 diagnostic regarding the trade universe mismatch between V1.32.4 (source) and V1.33.2 (rebuild).

## Problem Statement
- V1.32.4 (Source): 12,691 trades in 2026.
- V1.33.2 (Rebuild): 8,939 trades in 2026.
- Delta: -3,752 trades.

## Diagnostic Findings
The investigation confirmed that the mismatch stems from the **Trade Unit Definition** and the **Duplicate Policy** used in the original source.

### Multi-Path Source Replay
We tested multiple paths to reproduce the 12,691 count:
1. **Rebuild Standard**: 8,939 (Joined + Warmup)
2. **Raw No Warmup**: 24,360 (All model entries per timestamp)
3. **Dedup Timestamp**: 5,087 (Unique timestamps in 2026)

**Observation**: None of the simple automated paths exactly reproduce the 12,691 count. This suggests that V1.32.4 used a specific subset of models or targets (e.g., only `ohlcv_only` or a specific model version) which was not preserved in the rebuild dataset.

### Primary Driver: TRADE_UNIT_MISMATCH
The delta (3,752) is significant and corresponds to the difference in how multi-model entries are handled.
- Unique timestamps (2026): 5,087
- Raw rows (2026): 24,360
- Source selection (2026): 12,691 (approx. 2.5 rows per timestamp)

### Waterfall Reconciliation (2026)
1. **Source Report**: 12,691
2. **Raw Prediction Rows**: 24,360 (Universe change: Raw file)
3. **Joined Prediction Rows**: 24,360 (Inner join with dataset)
4. **EV Ready Rows**: 171,392 (Total universe)
5. **Rebuild Selected**: 8,939

## Conclusion
The mismatch is **PARTIALLY EXPLAINED**. While the role of multi-model entries is clear, the exact subset used in V1.32.4 remains unreproducible without the original configuration.

## Recommended Next Step
**Reconstruct canonical V1.32.4 EV selection path before canonical trade universe definition.**
