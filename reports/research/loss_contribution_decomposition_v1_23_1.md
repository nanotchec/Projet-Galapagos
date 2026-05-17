# Contribution Decomposition

```json
{
  "global_ranked_loss_drivers": [
    {
      "driver": "costs_dominate",
      "confidence": "strong"
    }
  ],
  "by_policy_loss_drivers": {
    "fixed_percent": [
      {
        "driver": "costs_dominate",
        "confidence": "strong"
      }
    ],
    "atr_proxy": [
      {
        "driver": "costs_dominate",
        "confidence": "strong"
      }
    ],
    "horizon_only": [
      {
        "driver": "costs_dominate",
        "confidence": "strong"
      }
    ]
  },
  "evidence": "Consensus across policies.",
  "confidence": "strong",
  "suggested_next_experiment": "Seek higher volatility setups or reduce trade frequency to outrun costs.",
  "do_not_do_next": [
    "Do not activate LLM reviewer.",
    "Do not execute holdout.",
    "Do not trade live."
  ]
}
```