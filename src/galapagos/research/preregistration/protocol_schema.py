from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationProtocol:
    version: str
    created_from: str
    candidate_filter: str
    candidate_policy: str
    protocol_locked: bool = True
    filter_parameters_locked: bool = True
    policy_parameters_locked: bool = True
    selection_rules_locked: bool = True
    metrics_locked: bool = True
    data_sources_locked: bool = True
    cost_model_locked: bool = True
    baselines_locked: bool = True
    no_hyperparameter_tuning: bool = True
    no_reviewer_llm: bool = True
    no_holdout: bool = True
    no_real_trading: bool = True
    success_criteria_complete: bool = True
    main_metric: str = "mean_net_pnl_after_cost_pct"
    
    locked_data_sources: dict[str, str] = field(default_factory=lambda: {
        "predictions": "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet",
        "research_dataset": (
            "data/gold/research_dataset/BTC/4h/"
            "research_dataset_with_alpha_scores.parquet"
        ),
        "intrabar": "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet",
        "trade_ledger_report": "reports/research/trade_ledger_intrabar_eval_v1_22_1.json"
    })
    
    locked_filter_definition: dict[str, Any] = field(default_factory=lambda: {
        "filter_name": "low_frequency_strict_score",
        "policy": "horizon_only",
        "score_column": "low_frequency_strict_score",
        "selection_logic": "fixed_percent_top_rank",
        "tie_break": "random_stable",
        "causal_only": True
    })
    
    forbidden_selection_columns: list[str] = field(default_factory=lambda: [
        "forward_return_*", "gross_pnl_pct", "net_pnl_pct", 
        "mfe_pct", "mae_pct", "exit_reason", 
        "simulation_status", "any realized future outcome"
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.version,
            "protocol_created_from": self.created_from,
            "candidate_filter": self.candidate_filter,
            "candidate_policy": self.candidate_policy,
            "protocol_locked": self.protocol_locked,
            "filter_parameters_locked": self.filter_parameters_locked,
            "policy_parameters_locked": self.policy_parameters_locked,
            "selection_rules_locked": self.selection_rules_locked,
            "metrics_locked": self.metrics_locked,
            "data_sources_locked": self.data_sources_locked,
            "cost_model_locked": self.cost_model_locked,
            "baselines_locked": self.baselines_locked,
            "no_hyperparameter_tuning": self.no_hyperparameter_tuning,
            "no_reviewer_llm": self.no_reviewer_llm,
            "no_holdout": self.no_holdout,
            "no_real_trading": self.no_real_trading,
            "success_criteria_complete": self.success_criteria_complete,
            "main_metric": self.main_metric,
            "locked_data_sources": self.locked_data_sources,
            "locked_filter_definition": self.locked_filter_definition,
            "forbidden_selection_columns": self.forbidden_selection_columns
        }
