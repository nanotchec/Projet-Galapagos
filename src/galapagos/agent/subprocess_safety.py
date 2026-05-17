from __future__ import annotations

import subprocess
import tempfile
import time
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path


class SubprocessSafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SafeSubprocessResult:
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    output_file_text: str | None
    output_file_used: str | None
    error: str | None = None


def require_read_only_sandbox(sandbox: str) -> None:
    if sandbox != "read-only":
        raise SubprocessSafetyError("Codex CLI sandbox must be read-only in V1.8C.")


def validate_prompt_size(prompt: str, max_prompt_chars: int) -> None:
    if max_prompt_chars <= 0:
        raise SubprocessSafetyError("max_prompt_chars must be positive.")
    if len(prompt) > max_prompt_chars:
        raise SubprocessSafetyError(
            f"Prompt length {len(prompt)} exceeds max_prompt_chars={max_prompt_chars}."
        )


def preview_text(text: str | bytes, limit: int = 2000) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def run_codex_exec_safely(
    command: Sequence[str],
    *,
    timeout_seconds: int,
    output_last_message: bool = True,
) -> SafeSubprocessResult:
    if timeout_seconds <= 0:
        raise SubprocessSafetyError("timeout_seconds is required and must be positive.")
    if not command or command[0] == "":
        raise SubprocessSafetyError("Command must be a non-empty argv list.")
    output_path: Path | None = None
    argv = list(command)
    if output_last_message:
        with tempfile.NamedTemporaryFile(
            prefix="galapagos_codex_cli_",
            suffix=".json",
            delete=False,
        ) as handle:
            output_path = Path(handle.name)
        prompt = argv.pop()
        argv.extend(["--output-last-message", str(output_path), prompt])
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
        output_text = None
        if output_path is not None and output_path.exists():
            output_text = output_path.read_text(encoding="utf-8", errors="replace")
        return SafeSubprocessResult(
            exit_code=completed.returncode,
            duration_seconds=time.perf_counter() - start,
            stdout=completed.stdout,
            stderr=completed.stderr,
            output_file_text=output_text,
            output_file_used=str(output_path) if output_path else None,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - start
        return SafeSubprocessResult(
            exit_code=None,
            duration_seconds=max(duration, float(timeout_seconds)),
            stdout=preview_text(exc.stdout or "", limit=1_000_000),
            stderr=preview_text(exc.stderr or "", limit=1_000_000),
            output_file_text=None,
            output_file_used=str(output_path) if output_path else None,
            error=f"Codex CLI timed out after {timeout_seconds} seconds.",
        )
    finally:
        if output_path is not None:
            with suppress(OSError):
                output_path.unlink(missing_ok=True)
