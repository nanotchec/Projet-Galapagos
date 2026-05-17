from __future__ import annotations


class BackfillRequestBuilder:
    """Builds the theoretical dry-run request plan based on priority gaps."""

    def __init__(self, backfill_plan: dict):
        self.priority_periods = backfill_plan.get("backfill_priority_periods", [])

    def analyze(self) -> dict:
        requests = []
        for period in self.priority_periods:
            if isinstance(period, str) and "2026" in period:
                requests.append({
                    "symbol": "BTCUSDT",
                    "timeframe": "1m",
                    "start_date": "2026-01-01",
                    "end_date": "2026-12-31",
                    "priority": "HIGH",
                    "reason": "Missing 2026 data"
                })

        return {
            "status": "BACKFILL_REQUEST_PLAN_BUILT_DRY_RUN",
            "planned_requests": requests,
            "symbols_targeted": ["BTCUSDT"],
            "timeframes_targeted": ["1m"]
        }
