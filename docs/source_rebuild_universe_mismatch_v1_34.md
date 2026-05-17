# Source/Rebuild Universe Mismatch Resolution - V1.34

This document summarizes the findings of the V1.34 diagnostic regarding the trade universe mismatch between V1.32.4 (source) and V1.33.2 (rebuild).

## Problem Statement
- V1.32.4 (Source): 12,691 trades in 2026.
- V1.33.2 (Rebuild): 8,939 trades in 2026.
- Delta: -3,752 trades.

## Diagnostic Findings
The investigation localized the mismatch to the **Trade Unit Definition** and **Join Path**.

### Primary Driver: TRADE_UNIT_MISMATCH
The core issue is that the V1.32.4 source environment treated each model/target combination (36 rows per 4h timestamp) as a separate trade opportunity, leading to higher counts. The V1.33.2 rebuild environment, through its strict merge with the research dataset, effectively enforced a more consistent trade unit, but the counts did not align due to differing duplicate policies.

### Secondary Drivers
- **JOIN_PATH_MISMATCH**: The inner join between raw predictions and the research dataset (required for feature alignment) resulted in the exclusion of timestamps not present in both files.
- **WARMUP_POLICY**: The 100-period warmup for EV proxies is correctly implemented but contributed to the overall delta when compared to the original source which may have had different warmup initialization.

## Reconcilation Waterfall (2026)
1. **Source Report**: 12,691
2. **Raw Predictions**: 24,360 (676 unique timestamps * 36 models)
3. **Rebuild Selected**: 8,939
4. **Final Delta**: -3,752

## Conclusion
The mismatch is **PARTIALLY EXPLAINED** by the trade unit multiplicity. V1.34 recommends formalizing the canonical trade universe before proceeding to payoff-aware research.

## Recommended Next Step
**Implement canonical trade universe definition, then rerun V1.32/V1.33 diagnostics.**
