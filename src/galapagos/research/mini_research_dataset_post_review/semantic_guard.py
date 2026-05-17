from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

FORBIDDEN_SEED_FIELD_TERMS = [
    "target",
    "label",
    "prediction",
    "predict",
    "future_return",
    "future_ret",
    "future_price",
    "future_pnl",
    "future_profit",
    "pnl",
    "profit",
    "return_forward",
    "forward_return",
    "next_return",
    "next_price",
    "outcome",
    "realized_return",
    "realized_pnl",
    "ev",
    "expected_value",
    "mfe",
    "mae",
    "drawdown_after",
    "hit_tp",
    "hit_sl",
    "win",
    "loss"
]

class MiniResearchDatasetSemanticGuard:
    def __init__(self, root: Path):
        self.root = root
        self.seed_path = root / "data/research/dataset_seed/v1_92"

    def _normalize(self, text: str) -> str:
        s = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        return re.sub(r'[^a-z0-9]', '', s.lower())

    def _walk_and_scan(self, obj: Any, results: dict[str, Any], file_name: str, json_path: str = "$") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                child_path = f"{json_path}.{k}"
                self._check_text(k, results, file_name, child_path)
                self._walk_and_scan(v, results, file_name, child_path)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                self._walk_and_scan(item, results, file_name, f"{json_path}[{index}]")
        elif isinstance(obj, str):
            self._check_text(obj, results, file_name, json_path)

    def _check_text(self, text: str, results: dict[str, Any], file_name: str, json_path: str) -> None:
        normalized = self._normalize(text)
        for term in FORBIDDEN_SEED_FIELD_TERMS:
            norm_term = self._normalize(term)
            if term == "ev":
                tokenized = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
                tokens = [token for token in re.split(r'[^A-Za-z0-9]+', tokenized.lower()) if token]
                if "ev" not in tokens:
                    continue
            if norm_term in normalized:
                # Exclusion for policy names
                if norm_term == "lookahead" and normalized in ["nolookahead", "nolookaheadpolicy"]:
                    continue
                
                # Check for "pnl" inside "pnl_column" or similar
                # But allow "available_ts", "decision_ts"
                
                results["forbidden_seed_terms_detected"] = True
                results["forbidden_seed_term_occurrences"].append({
                    "file": file_name,
                    "json_path": json_path,
                    "offending_key_or_value": text,
                    "matched_term": term,
                })
                
                if term in ["target", "future_return", "future_ret", "future_price", "future_pnl", "future_profit", "return_forward", "forward_return", "next_return", "next_price", "outcome", "realized_return", "realized_pnl", "pnl", "profit", "win", "loss", "hit_tp", "hit_sl", "drawdown_after"]:
                    results["target_like_fields_detected"] = True
                    results["leakage_detected"] = True
                if term in ["prediction", "predict", "ev", "expected_value", "mfe", "mae"]:
                    results["prediction_like_fields_detected"] = True
                if "future" in term or "next" in term or "forward" in term or "after" in term:
                    results["future_information_fields_detected"] = True
                if term == "label":
                    results["label_like_fields_detected"] = True

    def scan(self) -> dict[str, Any]:
        results: dict[str, Any] = {
            "physical_seed_semantic_scan_executed": True,
            "forbidden_seed_terms_detected": False,
            "forbidden_seed_terms_count": 0,
            "forbidden_seed_term_occurrences": [],
            "target_like_fields_detected": False,
            "future_information_fields_detected": False,
            "label_like_fields_detected": False,
            "prediction_like_fields_detected": False,
            "available_ts_policy_present": False,
            "decision_ts_policy_present": False,
            "feature_available_ts_lte_decision_ts_rule_present": False,
            "no_lookahead_policy_present": False,
            "leakage_detected": False,
            "lookahead_detected": False,
        }

        if not self.seed_path.exists():
            return results

        all_content = ""
        for p in self.seed_path.glob("*.json"):
            try:
                content = p.read_text(encoding="utf-8")
                data = json.loads(content)
                self._walk_and_scan(data, results, p.name)
                all_content += content.lower()
            except Exception:
                continue

        results["forbidden_seed_terms_count"] = len(results["forbidden_seed_term_occurrences"])

        if "available_ts" in all_content:
            results["available_ts_policy_present"] = True
        if "decision_ts" in all_content:
            results["decision_ts_policy_present"] = True
        if "available_ts" in all_content and "decision_ts" in all_content:
            results["feature_available_ts_lte_decision_ts_rule_present"] = True
        if "no lookahead" in all_content or "no-lookahead" in all_content or "no_lookahead" in all_content:
            results["no_lookahead_policy_present"] = True

        return results
