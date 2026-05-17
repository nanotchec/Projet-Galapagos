from datetime import UTC, datetime, timedelta

from galapagos.scheduler.local_scheduler import LocalScheduler, SchedulerConfig
from galapagos.scheduler.profile_lock import ProfileLock


def test_scheduler_once_runs_requested_profiles(tmp_path) -> None:
    calls: list[str] = []

    def fake_cycle_runner(**kwargs):
        calls.append(kwargs["profile"]["name"])
        return {"execution": {"action": "NO_TRADE"}}

    scheduler = LocalScheduler(
        SchedulerConfig(
            profiles=["30m", "4h"],
            database_path=str(tmp_path / "scheduler.sqlite"),
            once=True,
        ),
        cycle_runner=fake_cycle_runner,
        lock=ProfileLock(tmp_path / "locks"),
    )
    results = scheduler.run()
    assert calls == ["galapagos_30m", "galapagos_4h"]
    assert [result["status"] for result in results] == ["COMPLETED", "COMPLETED"]


def test_lock_blocks_double_cycle(tmp_path) -> None:
    lock = ProfileLock(tmp_path, stale_after_seconds=3600)
    first = lock.acquire("30m")
    second = lock.acquire("30m")
    assert first.acquired
    assert not second.acquired
    assert second.reason == "lock_recent"


def test_stale_lock_is_replaced(tmp_path) -> None:
    lock_path = tmp_path / "30m.lock"
    old = datetime.now(UTC) - timedelta(hours=2)
    lock_path.write_text(old.isoformat(), encoding="utf-8")
    result = ProfileLock(tmp_path, stale_after_seconds=60).acquire("30m")
    assert result.acquired
    assert result.stale_replaced

