from __future__ import annotations

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "galapagos"
__path__ = [str(_SRC_PACKAGE)]
__version__ = "0.1.0"
