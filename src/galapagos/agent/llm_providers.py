from __future__ import annotations

import json
import os
import shutil
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from galapagos.agent.subprocess_safety import (
    preview_text,
    require_read_only_sandbox,
    run_codex_exec_safely,
    validate_prompt_size,
)


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]], context: dict[str, Any]) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class LLMProviderResult:
    provider_name: str
    model: str | None
    reasoning_effort: str | None
    raw_response: str
    exit_code: int | None = None
    duration_seconds: float = 0.0
    stdout_preview: str = ""
    stderr_preview: str = ""
    output_file_used: str | None = None
    error: str | None = None
    available: bool = False


@dataclass(frozen=True)
class OpenAICodexProviderConfig:
    provider_name: str = "openai-codex"
    base_url: str | None = None
    auth_mode: str = "chatgpt_codex"
    model: str | None = None
    reasoning_effort: str = "low"
    temperature: float = 0.0
    max_tokens: int = 800
    timeout_seconds: int = 30
    max_retries: int = 1
    strict_json: bool = True
    allow_network_calls: bool = False
    endpoint_type: str = "responses"
    api_key_env: str | None = None

    @classmethod
    def from_sources(cls, config: dict[str, Any] | None = None) -> OpenAICodexProviderConfig:
        config = config or {}
        return cls(
            provider_name=str(
                config.get("provider_name") or config.get("provider") or "openai-codex"
            ),
            base_url=os.getenv("GALAPAGOS_OPENAI_CODEX_BASE_URL") or config.get("base_url"),
            auth_mode=os.getenv("GALAPAGOS_OPENAI_CODEX_AUTH_MODE")
            or str(config.get("auth_mode") or "chatgpt_codex"),
            model=os.getenv("GALAPAGOS_OPENAI_CODEX_MODEL") or config.get("model"),
            reasoning_effort=str(config.get("reasoning_effort") or "low"),
            temperature=float(config.get("temperature", 0.0)),
            max_tokens=int(config.get("max_tokens") or 800),
            timeout_seconds=int(
                os.getenv("GALAPAGOS_OPENAI_CODEX_TIMEOUT_SECONDS")
                or config.get("timeout_seconds")
                or 30
            ),
            max_retries=int(config.get("max_retries") or 1),
            strict_json=bool(config.get("strict_json", True)),
            allow_network_calls=bool(config.get("allow_network_calls", False)),
            endpoint_type=str(config.get("endpoint_type") or "responses"),
            api_key_env=config.get("api_key_env"),
        )


class OpenAICodexProvider(LLMProvider):
    """Configurable OpenClaw-like Codex provider interface."""

    def __init__(self, config: dict[str, Any] | OpenAICodexProviderConfig | None = None) -> None:
        self.config = (
            config
            if isinstance(config, OpenAICodexProviderConfig)
            else OpenAICodexProviderConfig.from_sources(config)
        )

    def complete(self, messages: list[dict[str, str]], context: dict[str, Any]) -> str:
        if not self.config.allow_network_calls:
            raise RuntimeError(
                "openai-codex provider is configured but network calls are disabled "
                "(allow_network_calls=false)."
            )
        if not self.config.base_url:
            raise RuntimeError(
                "openai-codex provider is configured but no local Codex/ChatGPT bridge is "
                "available yet."
            )
        if self.config.auth_mode == "chatgpt_codex":
            raise RuntimeError(
                "auth_mode=chatgpt_codex requires a Codex/ChatGPT runtime bridge that is not "
                "exposed to this local Python process yet. Use auth_mode=local_gateway or api_key "
                "with a compatible base_url when available."
            )
        if self.config.auth_mode not in {"api_key", "local_gateway"}:
            raise RuntimeError(f"Unsupported openai-codex auth_mode: {self.config.auth_mode}")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "reasoning": {"effort": self.config.reasoning_effort},
            "response_format": {"type": "json_object"} if self.config.strict_json else None,
            "metadata": {"galapagos_context": context},
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                return self._post_json(payload)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.config.max_retries:
                    time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(
            "openai-codex request failed after retries. "
            f"Last error: {last_error}"
        )

    @property
    def status(self) -> dict[str, Any]:
        return self.status_dict()

    def status_dict(self) -> dict[str, Any]:
        available = bool(
            self.config.allow_network_calls
            and self.config.base_url
            and self.config.auth_mode in {"api_key", "local_gateway"}
        )
        missing = []
        if not self.config.base_url:
            missing.append("base_url/local gateway")
        if not self.config.allow_network_calls:
            missing.append("allow_network_calls=true")
        if self.config.auth_mode == "chatgpt_codex":
            missing.append("ChatGPT/Codex runtime bridge exposed to Python")
        return {
            "provider": "openai-codex",
            "provider_name": self.config.provider_name,
            "available": available,
            "mode": self.config.auth_mode,
            "base_url_configured": bool(self.config.base_url),
            "model": self.config.model,
            "reasoning_effort": self.config.reasoning_effort,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "endpoint_type": self.config.endpoint_type,
            "allow_network_calls": self.config.allow_network_calls,
            "timeout_seconds": self.config.timeout_seconds,
            "max_retries": self.config.max_retries,
            "strict_json": self.config.strict_json,
            "missing": missing,
        }

    def diagnose(self) -> dict[str, Any]:
        status = self.status_dict()
        status["message"] = (
            "openai-codex provider is configured but no local Codex/ChatGPT bridge is "
            "available yet."
            if not status["available"]
            else "openai-codex provider appears configured for a network call."
        )
        status["secret_logging"] = "disabled"
        return status

    def _post_json(self, payload: dict[str, Any]) -> str:
        api_key_env = self.config.api_key_env or "GALAPAGOS_OPENAI_CODEX_API_KEY"
        api_key = os.getenv(api_key_env)
        headers = {"Content-Type": "application/json"}
        if self.config.auth_mode == "api_key":
            if not api_key:
                raise RuntimeError("auth_mode=api_key requires GALAPAGOS_OPENAI_CODEX_API_KEY")
            headers["Authorization"] = f"Bearer {api_key}"
        suffix = "/responses" if self.config.endpoint_type == "responses" else "/chat/completions"
        url = str(self.config.base_url).rstrip("/") + suffix
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        if self.config.endpoint_type == "responses":
            output_text = body.get("output_text")
            if isinstance(output_text, str):
                return output_text
        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("Provider response did not contain choices")
        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise RuntimeError("Provider response did not contain message.content")
        return content


@dataclass(frozen=True)
class CodexCLIProviderConfig:
    executable: str = "codex"
    model: str = "gpt-5.5"
    reasoning_effort: str = "low"
    sandbox: str = "read-only"
    skip_git_repo_check: bool = True
    output_last_message: bool = True
    timeout_seconds: int = 45
    max_prompt_chars: int = 12_000
    require_json_object: bool = True
    allow_codex_cli_calls: bool = False

    @classmethod
    def from_sources(cls, config: dict[str, Any] | None = None) -> CodexCLIProviderConfig:
        config = config or {}
        nested = config.get("codex_cli") or {}
        return cls(
            executable=str(nested.get("executable") or config.get("executable") or "codex"),
            model=str(nested.get("model") or config.get("model") or "gpt-5.5"),
            reasoning_effort=str(
                nested.get("reasoning_effort") or config.get("reasoning_effort") or "low"
            ),
            sandbox=str(nested.get("sandbox") or "read-only"),
            skip_git_repo_check=bool(nested.get("skip_git_repo_check", True)),
            output_last_message=bool(nested.get("output_last_message", True)),
            timeout_seconds=int(
                nested.get("timeout_seconds") or config.get("timeout_seconds") or 45
            ),
            max_prompt_chars=int(nested.get("max_prompt_chars") or 12_000),
            require_json_object=bool(nested.get("require_json_object", True)),
            allow_codex_cli_calls=bool(config.get("allow_codex_cli_calls", False)),
        )


class CodexCLIProvider(LLMProvider):
    """Local Codex CLI provider using codex exec through a guarded subprocess."""

    provider_name = "codex_cli"

    def __init__(self, config: dict[str, Any] | CodexCLIProviderConfig | None = None) -> None:
        self.config = (
            config
            if isinstance(config, CodexCLIProviderConfig)
            else CodexCLIProviderConfig.from_sources(config)
        )

    def complete(self, messages: list[dict[str, str]], context: dict[str, Any]) -> str:
        prompt = "\n\n".join(message.get("content", "") for message in messages)
        if not prompt:
            prompt = json.dumps(context, ensure_ascii=False, default=str)
        result = self.generate(prompt)
        if result.error:
            raise RuntimeError(result.error)
        return result.raw_response

    def generate(self, prompt: str) -> LLMProviderResult:
        start = time.monotonic()
        status = self.status
        if not self.config.allow_codex_cli_calls:
            return self._error_result(
                "codex_cli provider is configured but allow_codex_cli_calls=false.",
                start,
                available=status["available"],
            )
        if not status["executable_found"]:
            return self._error_result(
                f"Codex CLI executable not found: {self.config.executable}",
                start,
                available=False,
            )
        try:
            require_read_only_sandbox(self.config.sandbox)
            validate_prompt_size(prompt, self.config.max_prompt_chars)
        except Exception as exc:  # noqa: BLE001
            return self._error_result(str(exc), start, available=status["available"])

        command = self._build_command(prompt)
        safe_result = run_codex_exec_safely(
            command,
            timeout_seconds=self.config.timeout_seconds,
            output_last_message=self.config.output_last_message,
        )
        raw_response = (safe_result.output_file_text or safe_result.stdout or "").strip()
        error = safe_result.error
        if safe_result.exit_code not in {0, None} and error is None:
            error = f"Codex CLI exited with code {safe_result.exit_code}."
        if self.config.require_json_object and raw_response and "{" not in raw_response:
            error = error or "Codex CLI response does not contain a JSON object."
        if not raw_response and error is None:
            error = "Codex CLI did not produce an output_last_message response."
        return LLMProviderResult(
            provider_name=self.provider_name,
            model=self.config.model,
            reasoning_effort=self.config.reasoning_effort,
            raw_response=raw_response,
            exit_code=safe_result.exit_code,
            duration_seconds=round(safe_result.duration_seconds, 3),
            stdout_preview=preview_text(safe_result.stdout),
            stderr_preview=preview_text(safe_result.stderr),
            output_file_used=safe_result.output_file_used,
            error=error,
            available=status["available"],
        )

    @property
    def status(self) -> dict[str, Any]:
        executable_path = shutil.which(self.config.executable)
        available = bool(executable_path and self.config.sandbox == "read-only")
        return {
            "provider": self.provider_name,
            "available": available,
            "executable": self.config.executable,
            "executable_path": executable_path,
            "executable_found": bool(executable_path),
            "model": self.config.model,
            "reasoning_effort": self.config.reasoning_effort,
            "sandbox": self.config.sandbox,
            "skip_git_repo_check": self.config.skip_git_repo_check,
            "output_last_message": self.config.output_last_message,
            "timeout_seconds": self.config.timeout_seconds,
            "max_prompt_chars": self.config.max_prompt_chars,
            "require_json_object": self.config.require_json_object,
            "allow_codex_cli_calls": self.config.allow_codex_cli_calls,
        }

    def diagnose(self) -> dict[str, Any]:
        status = self.status
        status["message"] = (
            "codex_cli provider is available but real CLI calls are disabled by "
            "allow_codex_cli_calls=false."
            if status["available"] and not self.config.allow_codex_cli_calls
            else "codex_cli provider is ready for a guarded subprocess call."
            if status["available"]
            else "codex_cli provider is unavailable because the executable is missing."
        )
        status["secret_logging"] = "disabled"
        status["network_note"] = (
            "allow_network_calls is not used by codex_cli; Codex CLI may perform its own "
            "authenticated network call when allow_codex_cli_calls=true."
        )
        return status

    def _build_command(self, prompt: str) -> list[str]:
        command = [
            self.config.executable,
            "exec",
            "-m",
            self.config.model,
            "-c",
            f'model_reasoning_effort="{self.config.reasoning_effort}"',
        ]
        if self.config.skip_git_repo_check:
            command.append("--skip-git-repo-check")
        command.extend(["--sandbox", self.config.sandbox, prompt])
        return command

    def _error_result(
        self,
        error: str,
        start: float,
        *,
        available: bool,
    ) -> LLMProviderResult:
        return LLMProviderResult(
            provider_name=self.provider_name,
            model=self.config.model,
            reasoning_effort=self.config.reasoning_effort,
            raw_response="",
            duration_seconds=round(time.monotonic() - start, 3),
            error=error,
            available=available,
        )


class MockLLMProvider(LLMProvider):
    def __init__(self, decision: str = "NO_TRADE") -> None:
        self.decision = decision

    def complete(self, messages: list[dict[str, str]], context: dict[str, Any]) -> str:
        profile = context.get("profile", {})
        market = context.get("market", {})
        price = market.get("last_close")
        decision = self.decision.upper()
        if decision in {"LONG", "SHORT"} and price:
            is_long = decision == "LONG"
            payload = {
                "decision": decision,
                "profile": profile.get("name", "galapagos_30m"),
                "asset": profile.get("symbol", "BTC/USD"),
                "strategy": "breakout" if is_long else "momentum",
                "confidence": 0.61,
                "reasoning_summary": f"Mock {decision} decision for local development.",
                "horizon": profile.get("timeframe", "30m"),
                "reference_entry_price": price,
                "stop_loss": price * 0.99 if is_long else price * 1.01,
                "take_profit": price * 1.02 if is_long else price * 0.98,
                "risk_fraction": 0.0025,
                "max_duration_minutes": profile.get("max_position_duration_minutes", 240),
                "invalidation_conditions": ["Mock invalidation"],
                "critical_data_used": ["price", "volatility"],
            }
        elif decision == "CLOSE":
            payload = self._non_entry_payload(
                profile,
                "CLOSE",
                "close_position",
                "Mock close decision.",
            )
        elif decision == "HOLD":
            payload = self._non_entry_payload(
                profile,
                "HOLD",
                "risk_reduction",
                "Mock hold decision.",
            )
        else:
            payload = self._non_entry_payload(
                profile,
                "NO_TRADE",
                "no_trade",
                "Mock provider defaults to no trade.",
            )
        return json.dumps(payload)

    @property
    def status(self) -> dict[str, Any]:
        return {"provider": "mock", "available": True, "mode": "development_only"}

    def _non_entry_payload(
        self,
        profile: dict[str, Any],
        decision: str,
        strategy: str,
        summary: str,
    ) -> dict[str, Any]:
        return {
            "decision": decision,
            "profile": profile.get("name", "galapagos_30m"),
            "asset": profile.get("symbol", "BTC/USD"),
            "strategy": strategy,
            "confidence": 0.55,
            "reasoning_summary": summary,
            "horizon": profile.get("timeframe", "30m"),
            "reference_entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_fraction": 0.0,
            "max_duration_minutes": 0,
            "invalidation_conditions": [],
            "critical_data_used": [],
        }
