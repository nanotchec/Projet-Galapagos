# Feature Drift Analysis v1.17.1

Verdict: **FEATURE_DRIFT_DETECTED**

Analyzed 93 features. Found 19 significant drifts.
- Macro drifts: 0
- Derivatives drifts: 3

## Raw Payload
```json
{
  "version": "v1.17.1",
  "verdict": "FEATURE_DRIFT_DETECTED",
  "features_analyzed": 93,
  "significant_drifts": 19,
  "macro_drifts": 0,
  "deriv_drifts": 3,
  "drift_details": {
    "funding_rate_bybit": {
      "hist_mean": null,
      "rec_mean": -3.44978448275862e-06,
      "z_shift": 0.0,
      "missing_delta": -0.3222222222222222,
      "is_significant": true
    },
    "long_short_ratio_binance": {
      "hist_mean": null,
      "rec_mean": 0.8624190789473685,
      "z_shift": 0.0,
      "missing_delta": -0.21111111111111114,
      "is_significant": true
    },
    "open_interest_bybit": {
      "hist_mean": null,
      "rec_mean": 51375.981895348836,
      "z_shift": 0.0,
      "missing_delta": -0.23888888888888893,
      "is_significant": true
    },
    "taker_buy_sell_ratio_binance": {
      "hist_mean": null,
      "rec_mean": 1.031265359477124,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "taker_buy_volume_binance": {
      "hist_mean": null,
      "rec_mean": 12892.741503267973,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "taker_sell_volume_binance": {
      "hist_mean": null,
      "rec_mean": 12455.670307189543,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "long_short_ratio": {
      "hist_mean": null,
      "rec_mean": 0.8624190789473685,
      "z_shift": 0.0,
      "missing_delta": -0.21111111111111114,
      "is_significant": true
    },
    "open_interest": {
      "hist_mean": null,
      "rec_mean": 51375.981895348836,
      "z_shift": 0.0,
      "missing_delta": -0.23888888888888893,
      "is_significant": true
    },
    "taker_buy_sell_ratio": {
      "hist_mean": null,
      "rec_mean": 1.0312624806685475,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "taker_buy_volume": {
      "hist_mean": null,
      "rec_mean": 12892.741503267973,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "taker_sell_volume": {
      "hist_mean": null,
      "rec_mean": 12455.670307189543,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "open_interest_mean": {
      "hist_mean": null,
      "rec_mean": 51375.981895348836,
      "z_shift": 0.0,
      "missing_delta": -0.23888888888888893,
      "is_significant": true
    },
    "open_interest_change_3": {
      "hist_mean": null,
      "rec_mean": 0.00014798099338139063,
      "z_shift": 0.0,
      "missing_delta": -0.20833333333333337,
      "is_significant": true
    },
    "oi_change_3": {
      "hist_mean": null,
      "rec_mean": 0.00014798099338139063,
      "z_shift": 0.0,
      "missing_delta": -0.20833333333333337,
      "is_significant": true
    },
    "taker_imbalance": {
      "hist_mean": null,
      "rec_mean": 0.011538432902735186,
      "z_shift": 0.0,
      "missing_delta": -0.21250000000000002,
      "is_significant": true
    },
    "derivatives_confidence_score": {
      "hist_mean": 0.19999999999999996,
      "rec_mean": 0.3086111111111111,
      "z_shift": 1956294468821879.0,
      "missing_delta": -0.1719106247150023,
      "is_significant": true
    },
    "DFF": {
      "hist_mean": 4.6799042407660725,
      "rec_mean": 3.64,
      "z_shift": -1.94510746678478,
      "missing_delta": 0.0,
      "is_significant": true
    },
    "NASDAQCOM": {
      "hist_mean": 18849.309999999998,
      "rec_mean": 22986.494583333333,
      "z_shift": 1.7177263995773278,
      "missing_delta": 0.0,
      "is_significant": true
    },
    "SP500": {
      "hist_mean": 5816.130341997264,
      "rec_mean": 6842.742,
      "z_shift": 1.7946724278930586,
      "missing_delta": 0.0,
      "is_significant": true
    }
  }
}
```