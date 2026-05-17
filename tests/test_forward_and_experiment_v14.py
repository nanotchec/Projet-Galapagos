from dataclasses import asdict

from galapagos.experiments.experiment_runner import run_experiment
from galapagos.scheduler.local_scheduler import LocalScheduler, SchedulerConfig


def test_forward_paper_iterations_short(tmp_path) -> None:
    scheduler = LocalScheduler(
        SchedulerConfig(
            profiles=["30m"],
            database_path=str(tmp_path / "forward.sqlite"),
            once=True,
            use_real_data=False,
        )
    )
    results = scheduler.run()
    assert len(results) == 1
    assert results[0]["status"] == "COMPLETED"


def test_experiment_run_has_ids(tmp_path) -> None:
    result = run_experiment(
        {
            "experiment_name": "btc_30m_vs_4h",
            "experiment_id": "test-exp",
            "profiles": ["30m"],
            "use_real_data": False,
            "use_mock_llm": True,
        },
        database_path=str(tmp_path / "experiment.sqlite"),
        once=True,
        iterations=None,
        sleep_seconds=0,
        generate_report=False,
    )
    payload = asdict(result)
    assert payload["experiment_id"] == "test-exp"
    assert payload["run_id"]
    assert payload["total_cycles"] == 1

