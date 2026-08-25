"""Runtime NumPy import isolated from version-specific third-party type stubs."""

from __future__ import annotations

import importlib
from typing import Any, TypeAlias

np: Any = importlib.import_module("numpy")
NDArray: TypeAlias = Any
