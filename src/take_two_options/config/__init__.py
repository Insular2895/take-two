"""Versioned, fail-closed pre-OPRA configuration contracts."""

from take_two_options.config.contracts import PreOpraConfig
from take_two_options.config.loader import load_pre_opra_config

__all__ = ["PreOpraConfig", "load_pre_opra_config"]
