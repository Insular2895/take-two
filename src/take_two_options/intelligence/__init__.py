"""V11 probabilistic strategy intelligence and execution monitoring."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from take_two_options.intelligence.pipeline import run_intelligence


def __getattr__(name: str) -> Any:
    """Load the pipeline lazily so schema-only imports do not create cycles."""

    if name == "run_intelligence":
        from take_two_options.intelligence.pipeline import run_intelligence

        return run_intelligence
    raise AttributeError(name)

__all__ = ["run_intelligence"]
