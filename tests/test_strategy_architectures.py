from take_two_options.domain import StrategyKind
from take_two_options.strategy_architectures import (
    ARCHITECTURES,
    ArchitectureReadiness,
    architecture_for,
)


def test_architecture_catalog_separates_active_catalog_and_disabled_risk() -> None:
    assert len({item.kind for item in ARCHITECTURES}) == len(ARCHITECTURES)
    assert architecture_for(StrategyKind.CALL_BUTTERFLY).readiness is (
        ArchitectureReadiness.BACKTESTED
    )
    assert architecture_for(StrategyKind.PROTECTIVE_PUT).readiness is (
        ArchitectureReadiness.CATALOG_ONLY
    )
    assert architecture_for(StrategyKind.SHORT_STRADDLE).readiness is (
        ArchitectureReadiness.RISK_DISABLED
    )
