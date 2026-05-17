from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.daily_report import generate_daily_summary
from galapagos.scheduler.local_scheduler import LocalScheduler, SchedulerConfig
from galapagos.utils.paths import project_path
from galapagos.utils.time_utils import utc_now_iso


@dataclass(frozen=True)
class ExperimentRunResult:
    experiment_id: str
    run_id: str
    started_at: str
    ended_at: str
    profiles: list[str]
    database_path: str
    data_mode: str
    llm_provider: str
    total_cycles: int
    failed_cycles: int
    summary_metrics: dict[str, Any]
    report_paths: dict[str, str]


def run_experiment(
    experiment: dict[str, Any],
    *,
    database_path: str,
    once: bool,
    iterations: int | None,
    sleep_seconds: int,
    generate_report: bool,
) -> ExperimentRunResult:
    started_at = utc_now_iso()
    experiment_id = str(experiment.get("experiment_id") or experiment.get("experiment_name"))
    run_id = str(uuid4())
    profiles = list(experiment.get("profiles", ["30m", "4h"]))
    store = SQLiteStore(database_path)
    store.insert_system_event(
        {
            "timestamp_utc": started_at,
            "level": "INFO",
            "message": "experiment_started",
            "payload": {"experiment_id": experiment_id, "run_id": run_id, **experiment},
        }
    )
    scheduler = LocalScheduler(
        SchedulerConfig(
            profiles=profiles,
            database_path=database_path,
            use_real_data=bool(experiment.get("use_real_data", False)),
            use_mock_llm=bool(experiment.get("use_mock_llm", True)),
            mock_decision=str(experiment.get("mock_decision") or "NO_TRADE"),
            sleep_seconds=sleep_seconds,
            iterations=iterations,
            once=once,
        )
    )
    results = scheduler.run()
    failed = sum(1 for item in results if item.get("status") == "ERROR")
    report_paths = (
        generate_daily_summary(store, project_path("reports/daily")) if generate_report else {}
    )
    ended_at = utc_now_iso()
    return ExperimentRunResult(
        experiment_id=experiment_id,
        run_id=run_id,
        started_at=started_at,
        ended_at=ended_at,
        profiles=profiles,
        database_path=database_path,
        data_mode="real" if experiment.get("use_real_data") else "mock",
        llm_provider="mock" if experiment.get("use_mock_llm", True) else "openai-codex",
        total_cycles=len(results),
        failed_cycles=failed,
        summary_metrics={"completed_cycles": len(results) - failed},
        report_paths={key: str(value) for key, value in report_paths.items()},
    )

