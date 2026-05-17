"""Payoff-objective 2026 failure diagnostics for Galapagos V1.41."""
from __future__ import annotations

from .candidate_rebuilder import rebuild_candidate_diagnostic
from .cost_vs_gross_analysis import analyze_cost_vs_gross
from .data_loader import load_failure_diagnostic_inputs
from .diagnostic_verdict import build_failure_diagnostic_verdict
from .downside_miss_analysis import analyze_downside_miss
from .feature_shift_2026 import analyze_feature_shift
from .input_guard import build_failure_input_guard
from .label_noise_diagnostic import analyze_label_noise
from .ranking_quality_analysis import analyze_ranking_quality
from .regime_transfer_analysis import analyze_regime_transfer
from .report_writer import write_failure_diagnostic_report
from .score_decile_analysis import analyze_score_deciles

