"""Compatibility package pointing ``src.galapagos`` to ``galapagos`` modules."""
from __future__ import annotations

import galapagos as _galapagos

__path__ = _galapagos.__path__
