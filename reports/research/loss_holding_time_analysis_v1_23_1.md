# Holding Time Analysis

```json
{
  "by_policy": {
    "fixed_percent": {
      "buckets": {
        "1-3j": {
          "count": 1633,
          "mean": 0.002609919564777927,
          "sum": 4.261998649282355
        },
        "1-4h": {
          "count": 521,
          "mean": -0.011090211132437628,
          "sum": -5.778000000000004
        },
        "12-24h": {
          "count": 1016,
          "mean": -0.0003277559055118087,
          "sum": -0.33299999999999763
        },
        "4-12h": {
          "count": 1015,
          "mean": -0.0057192118226601025,
          "sum": -5.805000000000004
        },
        "< 1h": {
          "count": 90,
          "mean": -0.016000000000000004,
          "sum": -1.4400000000000004
        }
      },
      "mean_duration_seconds": 55630.52631578947,
      "median_duration_seconds": 62100.0,
      "verdict": "SHORT_HOLDING_UNPROFITABLE"
    },
    "atr_proxy": {
      "buckets": {
        "1-3j": {
          "count": 2414,
          "mean": 0.003939420085472656,
          "sum": 9.50976008633099
        },
        "1-4h": {
          "count": 223,
          "mean": -0.02095681644030991,
          "sum": -4.6733700661891096
        },
        "12-24h": {
          "count": 875,
          "mean": -0.005131209860137772,
          "sum": -4.48980862762055
        },
        "4-12h": {
          "count": 743,
          "mean": -0.012045258499416846,
          "sum": -8.949627065066716
        },
        "< 1h": {
          "count": 20,
          "mean": -0.022724171717214692,
          "sum": -0.45448343434429384
        }
      },
      "mean_duration_seconds": 67268.21052631579,
      "median_duration_seconds": 86400.0,
      "verdict": "SHORT_HOLDING_UNPROFITABLE"
    },
    "horizon_only": {
      "buckets": {
        "1-3j": {
          "count": 4275,
          "mean": -0.0016620411026697936,
          "sum": -7.105225713913367
        }
      },
      "mean_duration_seconds": 86400.0,
      "median_duration_seconds": 86400.0,
      "verdict": "HOLDING_TIME_NOT_PRIMARY_DRIVER"
    }
  },
  "verdict": "SHORT_HOLDING_UNPROFITABLE"
}
```