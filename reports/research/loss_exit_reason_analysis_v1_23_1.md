# Exit Reason Analysis

```json
{
  "by_policy": {
    "fixed_percent": {
      "reasons": {
        "stop_loss": {
          "net_pnl_pct_count": 1884,
          "net_pnl_pct_mean": -0.018000000000000016,
          "net_pnl_pct_sum": -33.91200000000003,
          "gross_pnl_pct_mean": -0.015000000000000013
        },
        "take_profit": {
          "net_pnl_pct_count": 763,
          "net_pnl_pct_mean": 0.027000000000000027,
          "net_pnl_pct_sum": 20.60100000000002,
          "gross_pnl_pct_mean": 0.030000000000000023
        },
        "timeout": {
          "net_pnl_pct_count": 1628,
          "net_pnl_pct_mean": 0.0025902940106156975,
          "net_pnl_pct_sum": 4.216998649282355,
          "gross_pnl_pct_mean": 0.005590294010615697
        }
      },
      "primary_loser_reason": "stop_loss",
      "verdict": "STOP_LOSS_DOMINATES_LOSSES"
    },
    "atr_proxy": {
      "reasons": {
        "stop_loss": {
          "net_pnl_pct_count": 1419,
          "net_pnl_pct_mean": -0.023723000432875212,
          "net_pnl_pct_sum": -33.66293761424993,
          "gross_pnl_pct_mean": -0.020723000432875213
        },
        "take_profit": {
          "net_pnl_pct_count": 448,
          "net_pnl_pct_mean": 0.03350573648747986,
          "net_pnl_pct_sum": 15.01056994639098,
          "gross_pnl_pct_mean": 0.036505736487479866
        },
        "timeout": {
          "net_pnl_pct_count": 2408,
          "net_pnl_pct_mean": 0.003984567508708168,
          "net_pnl_pct_sum": 9.594838560969269,
          "gross_pnl_pct_mean": 0.006984567508708168
        }
      },
      "primary_loser_reason": "stop_loss",
      "verdict": "STOP_LOSS_DOMINATES_LOSSES"
    },
    "horizon_only": {
      "reasons": {
        "horizon_timeout": {
          "net_pnl_pct_count": 4275,
          "net_pnl_pct_mean": -0.0016620411026697936,
          "net_pnl_pct_sum": -7.105225713913367,
          "gross_pnl_pct_mean": 0.0013379588973302067
        }
      },
      "primary_loser_reason": "horizon_timeout",
      "verdict": "HORIZON_ONLY_BEST_BUT_STILL_NEGATIVE"
    }
  },
  "verdict": "STOP_LOSS_DOMINATES_LOSSES"
}
```