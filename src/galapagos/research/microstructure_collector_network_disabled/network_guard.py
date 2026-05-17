from __future__ import annotations
import socket
from typing import Any


class NetworkDisabledError(RuntimeError):
    """Raised when a network call is attempted while network is disabled."""
    pass


def block_network() -> None:
    """Monkeys patches socket to prevent any network activity."""
    def guarded_socket(*args: Any, **kwargs: Any) -> Any:
        raise NetworkDisabledError("Network access is explicitly disabled in this version (V1.54).")

    socket.socket = guarded_socket  # type: ignore


class NetworkGuard:
    """Context manager to ensure network is disabled during a block of code."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.original_socket = socket.socket

    def __enter__(self) -> NetworkGuard:
        if self.enabled:
            block_network()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        socket.socket = self.original_socket
