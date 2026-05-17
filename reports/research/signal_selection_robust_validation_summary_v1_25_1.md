# Signal Selection Robust Validation Summary V1 25 1

```json
{
  "version": "v1.25.1",
  "candidate_filter": "low_frequency_strict_score",
  "temporal_robustness": {
    "2024": {
      "count": 53,
      "mean_pnl": 0.01159245231402171,
      "total_pnl": 0.6143999726431506,
      "win_rate": 0.5849056603773585
    },
    "2025": {
      "count": 52,
      "mean_pnl": 0.004557431735255791,
      "total_pnl": 0.23698645023330112,
      "win_rate": 0.5576923076923077
    },
    "2026": {
      "count": 17,
      "mean_pnl": 0.0063011115079344366,
      "total_pnl": 0.10711889563488543,
      "win_rate": 0.5882352941176471
    },
    "2024_2025": {
      "count": 105,
      "mean_pnl": 0.008108442122632873,
      "total_pnl": 0.8513864228764517,
      "win_rate": 0.5714285714285714
    },
    "2025_2026_YTD": {
      "count": 69,
      "mean_pnl": 0.004987033998089659,
      "total_pnl": 0.3441053458681865,
      "win_rate": 0.5652173913043478
    },
    "2024_H1": {
      "count": 27,
      "mean_pnl": 0.010896745299377173,
      "total_pnl": 0.2942121230831837,
      "win_rate": 0.5555555555555556
    },
    "2024_H2": {
      "count": 26,
      "mean_pnl": 0.012314917290767962,
      "total_pnl": 0.320187849559967,
      "win_rate": 0.6153846153846154
    },
    "2025_H1": {
      "count": 26,
      "mean_pnl": 0.008709377453232092,
      "total_pnl": 0.22644381378403436,
      "win_rate": 0.6153846153846154
    },
    "2025_H2": {
      "count": 26,
      "mean_pnl": 0.00040548601727949065,
      "total_pnl": 0.010542636449266757,
      "win_rate": 0.5
    }
  },
  "sf_random": {
    "baseline_type": "monthly_count_preserving_random",
    "frequency_granularity": "month",
    "preserves_exact_timestamps": false,
    "preserves_monthly_counts": true,
    "preserves_weekly_counts": false,
    "observed_mean": 0.007856600971404403,
    "random_mean": -0.0016309590519005617,
    "p95": 0.0020884839833784567,
    "p_value_estimate": 0.0,
    "verdict": "BEATS_MONTHLY_COUNT_RANDOM",
    "methodology_note": "This baseline only preserves density at monthly scale. It does not account for intraday or weekly seasonality."
  },
  "cost_sensitivity": {
    "observed_gross_mean": 0.010856600971404402,
    "observed_net_mean": 0.007856600971404403,
    "observed_cost_mean": 0.0030000000000000005,
    "inferred_cost_mean": 0.002999999999999999,
    "cost_columns_available": true,
    "cost_reconstruction_status": "COST_RECONSTRUCTION_OK",
    "sensitivity": {
      "cost_0.0%": {
        "mean_pnl": 0.010856600971404402,
        "total_pnl": 1.3245053185113371,
        "win_rate": 0.6147540983606558
      },
      "cost_0.1%": {
        "mean_pnl": 0.009856600971404403,
        "total_pnl": 1.2025053185113372,
        "win_rate": 0.6065573770491803
      },
      "cost_0.2%": {
        "mean_pnl": 0.008856600971404402,
        "total_pnl": 1.0805053185113371,
        "win_rate": 0.5901639344262295
      },
      "cost_0.3%": {
        "mean_pnl": 0.007856600971404403,
        "total_pnl": 0.9585053185113371,
        "win_rate": 0.5737704918032787
      },
      "cost_0.5%": {
        "mean_pnl": 0.005856600971404404,
        "total_pnl": 0.7145053185113373,
        "win_rate": 0.5655737704918032
      }
    },
    "break_even_cost_pct": 1.0856600971404402,
    "verdict": "COST_ROBUST_EDGE_CANDIDATE"
  },
  "placebo": {
    "random_same_count_placebo": {
      "placebo_type": "random_unconditional_pick",
      "re_applies_filter": false,
      "preserves_filter_logic": false,
      "observed": 0.007856600971404403,
      "p95": 0.0020235137349601294,
      "verdict": "PLACEBO_PARTIAL_PASS",
      "limitation": "Does not re-apply filter logic on shuffled data; only tests if count-based performance is outlier."
    },
    "random_weekly_pick_placebo": {
      "placebo_type": "random_stratified_weekly_pick",
      "re_applies_filter": false,
      "preserves_filter_logic": false,
      "observed": 0.007856600971404403,
      "mean": -0.0012098803140742063,
      "p95": 0.002963320363355899,
      "verdict": "PLACEBO_PARTIAL_PASS",
      "limitation": "Does not account for filter selection criteria beyond temporal density."
    },
    "placebo_status": "PLACEBO_PARTIAL"
  },
  "stability": {
    "top_month_contribution": 0.12779734281688007,
    "top_10_trades_contribution": 0.6165574626293503,
    "monthly_pnl": {
      "2024-01": 0.047605575975095626,
      "2024-02": 0.0841499229034003,
      "2024-03": 0.12249443278159616,
      "2024-04": 0.017518473107747172,
      "2024-05": 0.015790702649844307,
      "2024-06": 0.006653015665500139,
      "2024-07": 0.08440012074553442,
      "2024-08": 0.04405115967743186,
      "2024-09": -0.009276298224857479,
      "2024-10": 0.037601948864234354,
      "2024-11": 0.10097880369576588,
      "2024-12": 0.0624321148018579,
      "2025-01": 0.014217969485965681,
      "2025-02": 0.052777550380713745,
      "2025-03": 0.03922881701168601,
      "2025-04": 0.0730139042596494,
      "2025-05": 0.04254313622892088,
      "2025-06": 0.0046624364170986116,
      "2025-07": -0.005215915359713386,
      "2025-08": -0.006474538071853053,
      "2025-09": -0.01870074421282418,
      "2025-10": 0.045153800419222144,
      "2025-11": -0.029272239067327344,
      "2025-12": 0.025052272741762572,
      "2026-01": 0.008932537294640091,
      "2026-02": 0.05434754925644737,
      "2026-03": 0.019963426038584302,
      "2026-04": 0.02387538304521366
    },
    "performance_concentration_warning": true,
    "verdict": "PERFORMANCE_CONCENTRATED"
  },
  "overfit": {
    "rules_tested_count": 78,
    "multiple_testing_warning": true,
    "best_filter_beats_p95": true,
    "top_filter_rank": 1,
    "verdict": "MULTIPLE_TESTING_RISK_HIGH",
    "audit_note": "FILTER_NEEDS_OUT_OF_SAMPLE_CONFIRMATION"
  },
  "robustness_blockers": [
    "MULTIPLE_TESTING_RISK_HIGH",
    "PERFORMANCE_CONCENTRATED",
    "RECENT_SAMPLE_TOO_SMALL"
  ],
  "multiple_testing_warning": true,
  "performance_concentration_warning": true,
  "recent_window_warning": true,
  "final_verdict": "PROMISING_BUT_REQUIRES_OUT_OF_SAMPLE_CONFIRMATION",
  "ready_for_reviewer": false,
  "methodology_honesty": {
    "random_baseline": "monthly_count_preserving_random",
    "placebo_status": "PLACEBO_PARTIAL",
    "cost_audit": "COST_RECONSTRUCTION_OK"
  }
}
```