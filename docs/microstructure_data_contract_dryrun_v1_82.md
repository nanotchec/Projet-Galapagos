# Microstructure Data Contract Dry-Run V1.82
## Overview
This version performs a theoretical simulation of a microstructure data contract materialization.
## Theoretical Schema
{
  "timestamp": "datetime64[ns]",
  "symbol": "string",
  "bid_price": "float64",
  "ask_price": "float64",
  "bid_size": "float64",
  "ask_size": "float64",
  "trade_price": "float64",
  "trade_size": "float64",
  "regime_label": "int32"
}
## Theoretical Paths
[
  "data/microstructure/symbol=BTCUSDT/date=2026-05-15/data.parquet",
  "data/microstructure/symbol=ETHUSDT/date=2026-05-15/data.parquet"
]
## Safety Verdict
Verdict: V1_82_TINY_DATA_CONTRACT_DRY_RUN_PASSED