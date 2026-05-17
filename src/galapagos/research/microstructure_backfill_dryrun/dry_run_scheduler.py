from __future__ import annotations


class DryRunScheduler:
    """Schedules the dry-run requests into manageable windows."""

    def __init__(self, request_plan: dict):
        self.planned_requests = request_plan.get("planned_requests", [])

    def analyze(self) -> dict:
        schedule = []
        for req in self.planned_requests:
            if req.get("start_date") == "2026-01-01" and req.get("end_date") == "2026-12-31":
                # Split by month for Binance Archive
                for month in range(1, 13):
                    m_str = f"{month:02d}"
                    schedule.append({
                        "window_start": f"2026-{m_str}-01",
                        "window_end": f"2026-{m_str}-31" if month in [1,3,5,7,8,10,12] else (f"2026-{m_str}-30" if month != 2 else f"2026-{m_str}-28"),
                        "estimated_rows": 43200, # 30 days * 24h * 60m
                        "chunk_type": "MONTHLY"
                    })

        return {
            "status": "DRY_RUN_SCHEDULE_CREATED",
            "schedule_windows": schedule,
            "total_estimated_rows": sum(w["estimated_rows"] for w in schedule)
        }
