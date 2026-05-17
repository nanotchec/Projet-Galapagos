# Regime Failure Analysis v1.17.1

Verdict: **REGIME_OVERFIT_SUSPECTED**

### Trend Regime Stats (2026)
- **range**: 366 samples, Mean 12bar: 0.0008
- **uptrend**: 172 samples, Mean 12bar: -0.0037
- **downtrend**: 182 samples, Mean 12bar: -0.0054

## Raw Payload
```json
{
  "version": "v1.17.1",
  "verdict": "REGIME_OVERFIT_SUSPECTED",
  "regime_analysis": {
    "volatility_regime": {
      "2024": {
        "low": {
          "count": 852,
          "mean_forward_return_12bar": 0.0011976400101529232,
          "mean_forward_return_6bar": 0.0010168683631759062,
          "hit_rate_12bar": 0.42488262910798125
        },
        "high": {
          "count": 1344,
          "mean_forward_return_12bar": 0.007245894115862237,
          "mean_forward_return_6bar": 0.00344130715222905,
          "hit_rate_12bar": 0.5498511904761905
        }
      },
      "2025": {
        "high": {
          "count": 795,
          "mean_forward_return_12bar": 0.0006155843604245128,
          "mean_forward_return_6bar": 0.0007749147206428142,
          "hit_rate_12bar": 0.46037735849056605
        },
        "low": {
          "count": 1395,
          "mean_forward_return_12bar": -0.00026946244203068835,
          "mean_forward_return_6bar": -0.0003387339241334793,
          "hit_rate_12bar": 0.44731182795698926
        }
      },
      "2026": {
        "low": {
          "count": 405,
          "mean_forward_return_12bar": 0.0004322415938883434,
          "mean_forward_return_6bar": 0.0011075417289075932,
          "hit_rate_12bar": 0.4567901234567901
        },
        "high": {
          "count": 315,
          "mean_forward_return_12bar": -0.0048448421621957805,
          "mean_forward_return_6bar": -0.0033936316543423223,
          "hit_rate_12bar": 0.4444444444444444
        }
      }
    },
    "trend_regime": {
      "2024": {
        "range": {
          "count": 939,
          "mean_forward_return_12bar": 0.0066707374620245926,
          "mean_forward_return_6bar": 0.0026893348428246545,
          "hit_rate_12bar": 0.4994675186368477
        },
        "uptrend": {
          "count": 769,
          "mean_forward_return_12bar": 0.003560243328375914,
          "mean_forward_return_6bar": 0.002881277219304978,
          "hit_rate_12bar": 0.5097529258777633
        },
        "downtrend": {
          "count": 488,
          "mean_forward_return_12bar": 0.0036008634918175543,
          "mean_forward_return_6bar": 0.0015379120060734343,
          "hit_rate_12bar": 0.4918032786885246
        }
      },
      "2025": {
        "range": {
          "count": 1300,
          "mean_forward_return_12bar": -0.0005069998219584239,
          "mean_forward_return_6bar": -0.0005676210830223412,
          "hit_rate_12bar": 0.4453846153846154
        },
        "uptrend": {
          "count": 419,
          "mean_forward_return_12bar": -0.0038216081883704974,
          "mean_forward_return_6bar": -0.0016304948945867772,
          "hit_rate_12bar": 0.39618138424821003
        },
        "downtrend": {
          "count": 471,
          "mean_forward_return_12bar": 0.00504000649549441,
          "mean_forward_return_6bar": 0.003321885663494133,
          "hit_rate_12bar": 0.5201698513800425
        }
      },
      "2026": {
        "range": {
          "count": 366,
          "mean_forward_return_12bar": 0.0007549245813047333,
          "mean_forward_return_6bar": -0.0007277069873343229,
          "hit_rate_12bar": 0.4672131147540984
        },
        "uptrend": {
          "count": 172,
          "mean_forward_return_12bar": -0.003735856601040195,
          "mean_forward_return_6bar": -0.0004291061936469836,
          "hit_rate_12bar": 0.3953488372093023
        },
        "downtrend": {
          "count": 182,
          "mean_forward_return_12bar": -0.005389726929101725,
          "mean_forward_return_6bar": -0.0016005716512970578,
          "hit_rate_12bar": 0.4725274725274725
        }
      }
    }
  }
}
```