# Trade Ledger Intrabar Evaluation Summary - v1.20

## Data Coverage Honesty
> [!IMPORTANT]
> **Evaluated Ratio**: 5.82%
> The intrabar sample is too short to draw robust conclusions. 
> Only 74 candidates were evaluated out of 4275.

## Final Verdict
- **Comparison Verdict**: `TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT`
- **Policy Comparison Valid**: False
- **Best Policy (Observed)**: observed_only_fixed_percent

## Policy Performance (After Cost)

### fixed_percent
- **Win Rate**: 36.55%
- **Median PnL**: -1.8000%
- **MAE (Mean)**: 2.22%

### atr_proxy
- **Win Rate**: 37.75%
- **Median PnL**: -1.0707%
- **MAE (Mean)**: 2.22%

### horizon_only
- **Win Rate**: 46.18%
- **Median PnL**: -0.5533%
- **MAE (Mean)**: 2.22%

## Conclusion
Le système v1.20 ne peut toujours pas passer d'ordre réel. La couverture intrabar est insuffisante pour valider une politique de trading.
