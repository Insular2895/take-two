"""Build the real aligned baseline panel while keeping licensed rows private."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.config.loader import load_pre_opra_config
from take_two_options.historical_data.market_context import MarketContextDataset
from take_two_options.historical_data.option_observations import HistoricalOptionObservation
from take_two_options.validation.baseline_comparison import (
    ComparisonConventions,
    EffectiveSearchSpace,
    compare_with_baselines,
)
from take_two_options.validation.comparable_panel import (
    ComparablePanelSettings,
    build_comparable_panel,
    panel_return_series,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_jsonl(path: Path) -> list[HistoricalOptionObservation]:
    return [
        HistoricalOptionObservation.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _numeric(value: object, name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    config = load_pre_opra_config(arguments.config.resolve())
    settings_raw = cast(dict[str, Any], config.extensions.get("baseline_panel", {}))
    settings = ComparablePanelSettings.model_validate(
        {
            key: value
            for key, value in settings_raw.items()
            if key in ComparablePanelSettings.model_fields
        }
    )
    option_path = ROOT / str(
        config.extensions.get("option_normalization", {}).get(
            "private_output", "data/pre_opra/normalized_options.jsonl"
        )
    )
    context_path = ROOT / str(
        config.extensions.get("market_context", {}).get(
            "private_output", "data/pre_opra/market_context.json"
        )
    )
    output_path = ROOT / str(
        settings_raw.get("private_output", "data/pre_opra/comparable_panel.json")
    )
    report_path = ROOT / str(
        settings_raw.get("aggregate_report", "reports/pre_opra/baseline_comparison_2026-08-08.json")
    )
    panel = build_comparable_panel(
        _load_jsonl(option_path),
        MarketContextDataset.model_validate_json(context_path.read_text(encoding="utf-8")),
        settings,
        generated_at=datetime.combine(config.research_request.as_of, datetime.min.time(), UTC),
    )
    output_path.write_text(panel.model_dump_json(indent=2) + "\n", encoding="utf-8")
    series = panel_return_series(panel)
    contracts_considered = max(
        sum(len(outcome.legs) for outcome in observation.outcomes)
        for observation in panel.observations
    )
    trials = settings.random_draws + 4
    report = compare_with_baselines(
        series,
        ticker="TTWO",
        dataset_hash=panel.dataset_hash,
        conventions=ComparisonConventions(
            horizon=(
                "consecutive full-chain dates: prior EOD signal, next-chain entry, "
                "following-chain exit"
            ),
            capital=settings.capital_eur,
            currency="EUR",
            fees=(
                f"options {settings.commission_per_contract_side:.2f} USD commission plus "
                f"{settings.slippage_per_contract_side:.2f} USD slippage per contract-side"
            ),
            spread_assumption="longs buy ask/sell bid; shorts sell bid/buy ask",
            fx_policy="ECB USD per EUR observed with conservative next-day availability",
            entry_convention="execute on first full-chain date after signal availability",
            exit_convention="execute on the next full-chain date using conservative sides",
            target_return=_numeric(config.risk_profile.target_return.value, "target_return"),
            large_loss_threshold=_numeric(
                config.risk_profile.large_loss_threshold.value, "large_loss_threshold"
            ),
        ),
        search_space=EffectiveSearchSpace(
            strategies_considered=9,
            contracts_considered=contracts_considered,
            expirations_considered=1,
            parameter_sets_considered=1,
            model_sets_considered=1,
            exit_rules_considered=1,
            actual_trials=trials,
            cartesian_upper_bound=9 * contracts_considered,
        ),
        alpha=_numeric(config.validation_policy.significance_level.value, "significance_level"),
        minimum_material_uplift=_numeric(
            config.validation_policy.minimum_economic_materiality.value,
            "minimum_economic_materiality",
        ),
        bootstrap_samples=int(settings_raw.get("bootstrap_samples", 2000)),
        permutation_samples=int(settings_raw.get("permutation_samples", 4000)),
        seed=settings.seed,
        synthetic=False,
        license_status="to_review",
    )
    report_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Comparable panel: observations={len(panel.observations)}, "
        f"strategies={len(series)}, status={report.status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
