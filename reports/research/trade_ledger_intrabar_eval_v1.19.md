# Trade Ledger Intrabar Evaluation - v1.19

## Signal Audit
- **Raw signals**: 23426
- **Unique timestamps**: 4275
- **Policy**: max_predicted_probability

## Policy Performance Summary

### Policy: fixed_percent
- **Candidates**: 4275
- **Evaluated**: 74
- **Win Rate**: 45.95%
- **Mean PnL (After Cost)**: -0.0966%
- **Median PnL (After Cost)**: -0.5014%
- **MAE (Mean)**: 1.30%
- **MFE (Mean)**: 2.33%

### Policy: atr_proxy
- **Candidates**: 4275
- **Evaluated**: 74
- **Win Rate**: 54.05%
- **Mean PnL (After Cost)**: 0.1275%
- **Median PnL (After Cost)**: -0.1766%
- **MAE (Mean)**: 1.30%
- **MFE (Mean)**: 2.33%

### Policy: horizon_only
- **Candidates**: 4275
- **Evaluated**: 74
- **Win Rate**: 55.41%
- **Mean PnL (After Cost)**: 0.3759%
- **Median PnL (After Cost)**: -0.0444%
- **MAE (Mean)**: 1.30%
- **MFE (Mean)**: 2.33%

## Final Comparison
- **Best Policy**: horizon_only
- **Best Mean PnL**: 0.3759%
- **Verdict**: `HORIZON_ONLY_BETTER_THAN_TPSL`

## Conclusion
The horizon_only policy showed the best results in this sample.
Le système V1.19 ne peut toujours pas passer d'ordre réel.
