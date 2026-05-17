# Cost Failure Analysis v1.17.1

Verdict: **EDGE_EXISTS_BEFORE_COSTS_ONLY**

### Cost Impact by Year
- **2024**: Gross = 0.0049, Net = 0.0019
- **2025**: Gross = 0.0001, Net = -0.0029
- **2026**: Gross = -0.0019, Net = -0.0049

## Raw Payload
```json
{
  "version": "v1.17.1",
  "verdict": "EDGE_EXISTS_BEFORE_COSTS_ONLY",
  "cost_analysis": {
    "2024": {
      "gross_forward_return": 0.004899303725122557,
      "base_cost_adjusted_return": 0.0018993037251225572,
      "sensitivity": {
        "x0.5": {
          "assumed_cost": 0.0015,
          "adjusted_return": 0.0033993037251225573,
          "positive_after_costs": true,
          "fraction_of_positive_trades_destroyed": 0.040234702430846606
        },
        "x1.0": {
          "assumed_cost": 0.003,
          "adjusted_return": 0.0018993037251225572,
          "positive_after_costs": true,
          "fraction_of_positive_trades_destroyed": 0.07711651299245599
        },
        "x2.0": {
          "assumed_cost": 0.006,
          "adjusted_return": -0.0011006962748774428,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.1374685666387259
        },
        "x3.0": {
          "assumed_cost": 0.009000000000000001,
          "adjusted_return": -0.004100696274877444,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.20620284995808885
        }
      }
    },
    "2025": {
      "gross_forward_return": 5.182167118935031e-05,
      "base_cost_adjusted_return": -0.00294817832881065,
      "sensitivity": {
        "x0.5": {
          "assumed_cost": 0.0015,
          "adjusted_return": -0.0014481783288106498,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.05966162065894924
        },
        "x1.0": {
          "assumed_cost": 0.003,
          "adjusted_return": -0.00294817832881065,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.11843276936776491
        },
        "x2.0": {
          "assumed_cost": 0.006,
          "adjusted_return": -0.00594817832881065,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.21460373998219057
        },
        "x3.0": {
          "assumed_cost": 0.009000000000000001,
          "adjusted_return": -0.00894817832881065,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.31255565449688333
        }
      }
    },
    "2026": {
      "gross_forward_return": -0.0019156134670812869,
      "base_cost_adjusted_return": -0.004915613467081287,
      "sensitivity": {
        "x0.5": {
          "assumed_cost": 0.0015,
          "adjusted_return": -0.003415613467081287,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.031073446327683617
        },
        "x1.0": {
          "assumed_cost": 0.003,
          "adjusted_return": -0.004915613467081287,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.08192090395480225
        },
        "x2.0": {
          "assumed_cost": 0.006,
          "adjusted_return": -0.007915613467081287,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.18361581920903955
        },
        "x3.0": {
          "assumed_cost": 0.009000000000000001,
          "adjusted_return": -0.010915613467081288,
          "positive_after_costs": false,
          "fraction_of_positive_trades_destroyed": 0.2570621468926554
        }
      }
    }
  }
}
```