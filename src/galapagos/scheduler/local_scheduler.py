from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from galapagos.cycle import run_cycle
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.scheduler.profile_lock import ProfileLock
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path
from galapagos.utils.time_utils import utc_now_iso

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchedulerConfig:
    profiles: list[str]
    database_path: str
    use_real_data: bool = False
    use_mock_llm: bool = True
    mock_decision: str = "NO_TRADE"
    sleep_seconds: int = 60
    iterations: int | None = None
    once: bool = False
    lock_stale_after_seconds: int = 1800


class LocalScheduler:
    def __init__(
        self,
        config: SchedulerConfig,
        *,
        cycle_runner: Callable[..., dict[str, Any]] = run_cycle,
        lock: ProfileLock | None = None,
    ) -> None:
        self.config = config
        self.cycle_runner = cycle_runner
        self.store = SQLiteStore(config.database_path)
        self.lock = lock or ProfileLock(
            project_path("data/paper/locks"),
            config.lock_stale_after_seconds,
        )
        self.next_run_at = {profile: 0.0 for profile in config.profiles}

    def run(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        iteration = 0
        while True:
            results.extend(self.run_pending(force=self.config.once))
            iteration += 1
            if self.config.once:
                break
            if self.config.iterations is not None and iteration >= self.config.iterations:
                break
            time.sleep(self.config.sleep_seconds)
        return results

    def run_pending(self, *, force: bool = False) -> list[dict[str, Any]]:
        now = time.time()
        results: list[dict[str, Any]] = []
        for profile in self.config.profiles:
            interval = self._interval_seconds(profile)
            if not force and now < self.next_run_at.get(profile, 0.0):
                continue
            result = self.run_profile(profile)
            results.append(result)
            self.next_run_at[profile] = now + interval
        return results

    def run_profile(self, profile_name: str) -> dict[str, Any]:
        lock_result = self.lock.acquire(profile_name)
        if not lock_result.acquired:
            self._event(
                "WARNING",
                f"Cycle ignored for {profile_name}: {lock_result.reason}",
                {"profile": profile_name, "lock_path": str(lock_result.lock_path)},
            )
            return {"profile": profile_name, "status": "SKIPPED_LOCKED", "lock": lock_result.reason}

        self._event("INFO", f"Cycle started for {profile_name}", {"profile": profile_name})
        try:
            profile = load_profile(profile_name)
            result = self.cycle_runner(
                profile=profile,
                risk_config=load_yaml("configs/risk.yaml"),
                llm_config=load_yaml("configs/llm.yaml"),
                database_path=self.config.database_path,
                use_real_data=self.config.use_real_data,
                use_mock_llm=self.config.use_mock_llm,
                mock_decision=self.config.mock_decision,
            )
            self._event(
                "INFO",
                f"Cycle finished for {profile_name}",
                {"profile": profile_name, "execution": result.get("execution")},
            )
            return {"profile": profile_name, "status": "COMPLETED", "result": result}
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Cycle failed for %s", profile_name)
            self._event("ERROR", f"Cycle failed for {profile_name}", {"error": str(exc)})
            return {"profile": profile_name, "status": "ERROR", "error": str(exc)}
        finally:
            self.lock.release(profile_name)

    def _interval_seconds(self, profile_name: str) -> int:
        profile = load_profile(profile_name)
        return int(profile.get("check_interval_minutes", 30)) * 60

    def _event(self, level: str, message: str, payload: dict[str, Any]) -> None:
        self.store.insert_system_event(
            {
                "timestamp_utc": utc_now_iso(),
                "level": level,
                "message": message,
                "payload": payload,
            }
        )
        getattr(LOGGER, level.lower(), LOGGER.info)(message)
