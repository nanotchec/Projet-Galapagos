from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class LockResult:
    acquired: bool
    profile: str
    lock_path: Path
    reason: str
    stale_replaced: bool = False


class ProfileLock:
    def __init__(self, lock_dir: str | Path, stale_after_seconds: int = 1800) -> None:
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.stale_after = timedelta(seconds=stale_after_seconds)

    def acquire(self, profile: str) -> LockResult:
        lock_path = self.lock_dir / f"{profile}.lock"
        now = datetime.now(UTC)
        if lock_path.exists():
            created_at = self._read_timestamp(lock_path)
            if created_at and now - created_at < self.stale_after:
                return LockResult(False, profile, lock_path, "lock_recent")
            lock_path.unlink(missing_ok=True)
            result = self._create_lock(lock_path, now, profile)
            return LockResult(
                result.acquired,
                profile,
                lock_path,
                "lock_stale_replaced" if result.acquired else result.reason,
                stale_replaced=result.acquired,
            )
        return self._create_lock(lock_path, now, profile)

    def release(self, profile: str) -> None:
        (self.lock_dir / f"{profile}.lock").unlink(missing_ok=True)

    def _create_lock(self, lock_path: Path, now: datetime, profile: str) -> LockResult:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return LockResult(False, profile, lock_path, "lock_created_by_other_process")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(now.isoformat())
        return LockResult(True, profile, lock_path, "lock_acquired")

    def _read_timestamp(self, lock_path: Path) -> datetime | None:
        try:
            return datetime.fromisoformat(lock_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

