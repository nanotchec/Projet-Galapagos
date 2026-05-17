# Intrabar Cost Model v1.19.2

Verdict: **INTRABAR_COST_PROXY_AVAILABLE**

## JSON Payload
```json
{
  "verdict": "INTRABAR_COST_PROXY_AVAILABLE",
  "note": "high-low range is not bid/ask spread. This is an intrabar_range_volatility_proxy.",
  "cost_proxy_type": "intrabar_range_volatility_proxy",
  "details": {
    "mean_intrabar_range_pct": 0.0014169817429756898,
    "base_cost_threshold": 0.003,
    "cost_stress_x2": 0.006,
    "cost_stress_x3": 0.009000000000000001
  }
}
```
