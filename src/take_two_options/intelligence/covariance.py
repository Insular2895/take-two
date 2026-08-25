"""Dynamic, shrinkage-regularized covariance with explicit observation windows."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.intelligence._numpy import NDArray, np
from take_two_options.intelligence.schemas import (
    CovarianceWindow,
    DynamicCovarianceReport,
)


class CovarianceDataError(ValueError):
    """Raised when factor history violates the point-in-time covariance contract."""


def load_factor_history(
    path: Path,
    *,
    cutoff: datetime,
) -> tuple[dict[str, list[float]], list[int], list[int]]:
    """Load aligned factor observations and optional event/regime row indices."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = [
            item
            for item in payload["rows"]
            if datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00")) <= cutoff
        ]
        factors = [str(item) for item in payload["factors"]]
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise CovarianceDataError(f"invalid factor history {path}: {error}") from error
    if not rows:
        raise CovarianceDataError("factor history has no pre-cutoff observations")
    series = {
        factor: [float(cast(dict[str, Any], row["values"])[factor]) for row in rows]
        for factor in factors
    }
    event_indices = [index for index, row in enumerate(rows) if bool(row.get("event_window"))]
    regime_indices = [index for index, row in enumerate(rows) if bool(row.get("current_regime"))]
    return series, event_indices, regime_indices


def _sample_covariance(matrix: NDArray) -> NDArray:
    if matrix.shape[0] < 2:
        raise CovarianceDataError("a covariance window needs at least two rows")
    if matrix.shape[1] == 1:
        return np.array([[float(np.var(matrix[:, 0], ddof=1))]], dtype=float)
    return np.asarray(np.cov(matrix, rowvar=False, ddof=1), dtype=float)


def _correlation(covariance: NDArray) -> NDArray:
    diagonal = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    denominator = np.outer(diagonal, diagonal)
    result = np.divide(
        covariance,
        denominator,
        out=np.zeros_like(covariance),
        where=denominator > 0,
    )
    np.fill_diagonal(result, np.where(diagonal > 0, 1.0, 0.0))
    return result


def dynamic_covariance(
    factor_history: dict[str, list[float]],
    *,
    windows: list[int],
    shrinkage: float,
    event_indices: list[int] | None = None,
    regime_indices: list[int] | None = None,
) -> DynamicCovarianceReport:
    """Blend recent, long, event, and current-regime samples then project to PSD."""
    if not factor_history:
        return DynamicCovarianceReport(
            status="insufficient_data",
            factors=[],
            windows=[],
            shrunk_covariance=[],
            correlation=[],
            shrinkage_intensity=shrinkage,
            minimum_eigenvalue=0.0,
            condition_number=None,
            warnings=["No aligned factor history was supplied."],
        )
    factors = list(factor_history)
    lengths = {len(factor_history[factor]) for factor in factors}
    if len(lengths) != 1:
        raise CovarianceDataError("all factor series must have the same length")
    observations = lengths.pop()
    if observations < 2:
        return DynamicCovarianceReport(
            status="insufficient_data",
            factors=factors,
            windows=[],
            shrunk_covariance=[],
            correlation=[],
            shrinkage_intensity=shrinkage,
            minimum_eigenvalue=0.0,
            condition_number=None,
            warnings=["Fewer than two aligned factor observations."],
        )
    matrix = np.column_stack(
        [np.asarray(factor_history[factor], dtype=float) for factor in factors]
    )
    if not np.isfinite(matrix).all():
        raise CovarianceDataError("factor history contains non-finite values")

    samples: list[tuple[str, NDArray, int, float]] = []
    recency_weights = [0.45, 0.35, 0.20]
    for index, window in enumerate(windows):
        if observations < min(window, 2):
            continue
        sample = matrix[-min(window, observations) :]
        weight = recency_weights[index] if index < len(recency_weights) else 0.10
        samples.append((f"{window}_sessions", _sample_covariance(sample), len(sample), weight))
    for label, indices, weight in (
        ("comparable_events", event_indices or [], 0.25),
        ("current_regime", regime_indices or [], 0.30),
    ):
        valid_indices = sorted({item for item in indices if 0 <= item < observations})
        if len(valid_indices) >= 2:
            sample = matrix[valid_indices]
            samples.append((label, _sample_covariance(sample), len(sample), weight))
    if not samples:
        return DynamicCovarianceReport(
            status="insufficient_data",
            factors=factors,
            windows=[],
            shrunk_covariance=[],
            correlation=[],
            shrinkage_intensity=shrinkage,
            minimum_eigenvalue=0.0,
            condition_number=None,
            warnings=["No requested covariance window had enough observations."],
        )
    total_weight = sum(item[3] for item in samples)
    normalized = [
        (label, covariance, count, weight / total_weight)
        for label, covariance, count, weight in samples
    ]
    blended = sum(weight * covariance for _, covariance, _, weight in normalized)
    diagonal_target = np.diag(np.diag(blended))
    shrunk = (1.0 - shrinkage) * blended + shrinkage * diagonal_target
    eigenvalues, eigenvectors = np.linalg.eigh(shrunk)
    scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
    floor = scale * 1e-10
    clipped = np.maximum(eigenvalues, floor)
    projected = eigenvectors @ np.diag(clipped) @ eigenvectors.T
    projected = (projected + projected.T) / 2
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(projected)))
    condition_number = float(np.linalg.cond(projected))
    warnings: list[str] = []
    status: str = "ready"
    if observations < max(windows):
        status = "partial"
        warnings.append(
            f"Only {observations} rows available; the {max(windows)}-session window is partial."
        )
    if event_indices is None or len(event_indices) < 2:
        status = "partial"
        warnings.append("Comparable-event covariance was not available.")
    if regime_indices is None or len(regime_indices) < 2:
        status = "partial"
        warnings.append("Current-regime subset was not available.")
    if not math.isfinite(condition_number) or condition_number > 1e8:
        warnings.append("Covariance remains ill-conditioned after shrinkage.")
    return DynamicCovarianceReport(
        status=cast(Any, status),
        factors=factors,
        windows=[
            CovarianceWindow(
                label=label,
                observations=count,
                weight=weight,
                covariance=covariance.tolist(),
            )
            for label, covariance, count, weight in normalized
        ],
        shrunk_covariance=projected.tolist(),
        correlation=_correlation(projected).tolist(),
        shrinkage_intensity=shrinkage,
        minimum_eigenvalue=minimum_eigenvalue,
        condition_number=condition_number if math.isfinite(condition_number) else None,
        warnings=warnings,
    )
