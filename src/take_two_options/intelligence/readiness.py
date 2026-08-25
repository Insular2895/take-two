"""Product-readiness inventory that never promotes synthetic research outputs."""

from __future__ import annotations

from take_two_options.intelligence.backtesting import WalkForwardReport
from take_two_options.intelligence.calibration import OfflineCalibrationReport
from take_two_options.intelligence.schemas import (
    ConnectorState,
    FeatureReadiness,
    FeatureStatus,
    LocalVolatilityCalibrationReport,
    UnifiedDataSnapshot,
)


def build_readiness_inventory(
    *,
    data_snapshot: UnifiedDataSnapshot,
    local_volatility: LocalVolatilityCalibrationReport,
    calibration: OfflineCalibrationReport,
    backtest: WalkForwardReport,
) -> list[FeatureReadiness]:
    connector_states = {
        connector.connector_id: connector.state for connector in data_snapshot.connectors
    }
    synthetic = any(source.quality.value == "synthetic" for source in data_snapshot.sources)
    return [
        FeatureReadiness(
            feature="v10_1_contractual_engine",
            status=FeatureStatus.PRODUCTION_READY_OFFLINE,
            implemented=True,
            evidence=[
                "Bounded structures, conservative entry cost, exact payoff, "
                "and QuantLib American control are covered by offline tests."
            ],
        ),
        FeatureReadiness(
            feature="unified_data_provenance",
            status=FeatureStatus.PRODUCTION_READY_OFFLINE,
            implemented=True,
            evidence=[
                "Final observations include provider, retrieval time, cutoff, "
                "freshness, raw hash, source, unit, and point-in-time validity."
            ],
            blockers=list(data_snapshot.missing_required_series),
        ),
        FeatureReadiness(
            feature="deterministic_event_normalization",
            status=FeatureStatus.EXPERIMENTAL_OFFLINE,
            implemented=True,
            evidence=[
                "Rule proofs, duplicate clusters, contradiction clusters, expiry, "
                "and human-review states are deterministic."
            ],
            blockers=["Likelihood impact still requires calibrated rules and reviewed events."],
        ),
        FeatureReadiness(
            feature="bayesian_scenario_engine",
            status=FeatureStatus.EXPERIMENTAL_OFFLINE,
            implemented=True,
            evidence=["Full weight waterfall and sensitivity bounds are serialized."],
            blockers=["Priors and likelihoods are not historically calibrated."],
        ),
        FeatureReadiness(
            feature="multi_model_simulation",
            status=(
                FeatureStatus.FIXTURE_ONLY
                if synthetic
                else FeatureStatus.EXPERIMENTAL_OFFLINE
            ),
            implemented=True,
            evidence=["Seeded GBM, local volatility, Heston, and Heston+jumps run offline."],
            blockers=[
                "Parameters require historical calibration and convergence review.",
                *(
                    ["Local-volatility input is not arbitrage-free."]
                    if not local_volatility.arbitrage_free_input
                    else []
                ),
            ],
        ),
        FeatureReadiness(
            feature="historical_calibration",
            status=FeatureStatus.REQUIRES_HISTORICAL_CALIBRATION,
            implemented=True,
            evidence=["CSV/JSON/optional Parquet validation and fail-closed fit workflow exist."],
            blockers=[calibration.status],
        ),
        FeatureReadiness(
            feature="walk_forward_backtest",
            status=FeatureStatus.REQUIRES_HISTORICAL_CALIBRATION,
            implemented=True,
            evidence=[
                "Point-in-time cases, prudent bid/ask, costs, baselines, "
                "calibration metrics, and locked holdout contracts exist."
            ],
            blockers=[backtest.status],
        ),
        FeatureReadiness(
            feature="exact_integer_allocation",
            status=FeatureStatus.EXPERIMENTAL_OFFLINE,
            implemented=True,
            evidence=[
                "Budget, loss, contracts, positions, concentration, liquidity, "
                "Greek exposure, cash, and NO_TRADE are hard constraints."
            ],
            blockers=["Objective inputs remain experimental until model validation."],
        ),
        FeatureReadiness(
            feature="position_monitoring",
            status=FeatureStatus.EXPERIMENTAL_OFFLINE,
            implemented=True,
            evidence=["Snapshot replay and configurable advisory exit rules are offline."],
            blockers=["Live/paper trajectory evidence has not been completed."],
        ),
        FeatureReadiness(
            feature="standalone_reporting",
            status=FeatureStatus.PRODUCTION_READY_OFFLINE,
            implemented=True,
            evidence=["JSON, Markdown, HTML, machine summary, versions, and hashes are emitted."],
        ),
        FeatureReadiness(
            feature="ibkr_opra_read_only_adapter",
            status=FeatureStatus.ADAPTER_READY_NOT_CONNECTED,
            implemented=True,
            evidence=["Market-data-only port exists and order-capable adapters are rejected."],
            blockers=[
                connector_states.get(
                    "ibkr_opra_read_only",
                    ConnectorState.NOT_CONFIGURED,
                ).value
            ],
        ),
        FeatureReadiness(
            feature="live_market_data",
            status=FeatureStatus.REQUIRES_LIVE_MARKET_DATA,
            implemented=False,
            blockers=["OPRA entitlements, TWS/IB Gateway session, and combo quotes are absent."],
        ),
        FeatureReadiness(
            feature="paper_trading_validation",
            status=FeatureStatus.REQUIRES_PAPER_TRADING,
            implemented=False,
            blockers=["No minimum-duration paper campaign has been completed."],
        ),
        FeatureReadiness(
            feature="order_execution",
            status=FeatureStatus.BLOCKED_FOR_EXECUTION,
            implemented=False,
            evidence=[
                "transmit=false, what_if=true, human confirmation, "
                "and order_capability=forbidden are invariant."
            ],
            blockers=["Execution is outside this product version by explicit policy."],
        ),
    ]
