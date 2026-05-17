# Walk Forward Calibration Comparison - v1.31.1

```json
[
  {
    "method": "raw_probability",
    "mean_brier": 0.2889913457879318,
    "mean_ece": 0.15134236676612386,
    "mean_mce": 0.41793930502205995,
    "sample_count": 134436
  },
  {
    "method": "isotonic_regression",
    "mean_brier": 0.2413413073864606,
    "mean_ece": 0.029688149711737995,
    "mean_mce": 0.6084242861587554,
    "sample_count": 134436
  },
  {
    "method": "bin_calibration",
    "mean_brier": 0.2409716462519486,
    "mean_ece": 0.030834044705496066,
    "mean_mce": 0.07410343033196395,
    "sample_count": 134436
  },
  {
    "method": "platt_scaling",
    "mean_brier": 0.24189328432693588,
    "mean_ece": 0.02923227490249583,
    "mean_mce": 0.09470992322808004,
    "sample_count": 134436
  }
]
```
