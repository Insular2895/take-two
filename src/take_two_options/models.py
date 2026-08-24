"""Shared strict Pydantic base without domain-module import cycles."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Reject unknown fields and validate assignments across financial contracts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
