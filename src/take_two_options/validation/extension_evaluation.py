"""Fail-closed Phase-11 gate for advanced quantitative model extensions."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel

ExtensionStatus = Literal["reject", "defer", "prototype", "candidate_for_implementation"]


class ExtensionGateEvidence(StrictModel):
    authorized_data_ready: bool = False
    identifiable_against_baseline: bool = False
    oos_material_gain_demonstrated: bool = False
    ranking_sensitivity_completed: bool = False
    numerical_cost_benchmarked: bool = False
    independent_review_completed: bool = False
    synthetic_prototype_completed: bool = False

    @property
    def candidate_ready(self) -> bool:
        return all(
            (
                self.authorized_data_ready,
                self.identifiable_against_baseline,
                self.oos_material_gain_demonstrated,
                self.ranking_sensitivity_completed,
                self.numerical_cost_benchmarked,
                self.independent_review_completed,
            )
        )


def classify_extension(
    evidence: ExtensionGateEvidence, *, out_of_scope_current_release: bool
) -> ExtensionStatus:
    """Classify without treating documentary availability as evidence of value."""
    if evidence.candidate_ready:
        return "candidate_for_implementation"
    if evidence.synthetic_prototype_completed:
        return "prototype"
    if out_of_scope_current_release:
        return "reject"
    return "defer"


class AdvancedExtensionAssessment(StrictModel):
    extension_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    scope: Literal["current_ttwo_research_release"] = "current_ttwo_research_release"
    out_of_scope_current_release: bool
    status: ExtensionStatus
    source_ids: list[str] = Field(min_length=1)
    data_requirements: list[str] = Field(min_length=1)
    comparison_baseline: str = Field(min_length=1)
    evidence: ExtensionGateEvidence
    blockers: list[str] = Field(min_length=1)
    reconsideration_gate: str = Field(min_length=1)
    implementation_allowed: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def require_computed_status(self) -> AdvancedExtensionAssessment:
        expected = classify_extension(
            self.evidence,
            out_of_scope_current_release=self.out_of_scope_current_release,
        )
        if self.status != expected:
            raise ValueError(f"status {self.status} exceeds computed status {expected}")
        if self.status == "candidate_for_implementation" and self.blockers:
            raise ValueError("implementation candidates cannot retain blockers")
        return self


class Phase11ExtensionReview(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    reviewed_on: Literal["2026-08-08"] = "2026-08-08"
    overall_status: Literal["NO_ADVANCED_MODEL_IMPLEMENTATION"]
    maximum_claim: Literal["documentary_gate_only"]
    assessments: list[AdvancedExtensionAssessment] = Field(min_length=1)
    candidate_for_implementation: list[str]
    integrated_advanced_models: list[str] = Field(max_length=0)
    implementation_allowed: Literal[False] = False
    source_limitations: list[str] = Field(min_length=1)
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def require_unique_and_exact_candidates(self) -> Phase11ExtensionReview:
        ids = [item.extension_id for item in self.assessments]
        if len(ids) != len(set(ids)):
            raise ValueError("extension IDs must be unique")
        computed = sorted(
            item.extension_id
            for item in self.assessments
            if item.status == "candidate_for_implementation"
        )
        if self.candidate_for_implementation != computed:
            raise ValueError("candidate list must match computed assessment statuses")
        return self


def _assessment(
    *,
    extension_id: str,
    label: str,
    source_ids: list[str],
    data_requirements: list[str],
    comparison_baseline: str,
    blockers: list[str],
    reconsideration_gate: str,
    out_of_scope: bool = False,
) -> AdvancedExtensionAssessment:
    evidence = ExtensionGateEvidence()
    return AdvancedExtensionAssessment(
        extension_id=extension_id,
        label=label,
        out_of_scope_current_release=out_of_scope,
        status=classify_extension(
            evidence,
            out_of_scope_current_release=out_of_scope,
        ),
        source_ids=source_ids,
        data_requirements=data_requirements,
        comparison_baseline=comparison_baseline,
        evidence=evidence,
        blockers=blockers,
        reconsideration_gate=reconsideration_gate,
    )


def build_phase11_extension_review() -> Phase11ExtensionReview:
    """Return the current evidence-based extension decisions; integrate no model."""
    assessments = [
        _assessment(
            extension_id="bergomi_forward_variance",
            label="Bergomi forward-variance dynamics",
            source_ids=["book-bergomi-stochastic-volatility-modeling"],
            data_requirements=[
                "multi-date arbitrage-screened TTWO option surfaces",
                "observable variance or smile-dynamics hedging targets",
            ],
            comparison_baseline="validated Heston plus SVI surface",
            blockers=[
                "Heston has not passed a real TTWO calibration gate",
                "no TTWO forward-variance or smile-dynamics history is available",
            ],
            reconsideration_gate="Show stable OOS pricing and ranking gain versus Heston/SVI.",
        ),
        _assessment(
            extension_id="rough_bergomi",
            label="Rough Bergomi volatility",
            source_ids=[
                "paper-gatheral-jaisson-rosenbaum-volatility-rough",
                "paper-bayer-friz-gatheral-pricing-rough-volatility",
                "paper-livieri-mouti-pallavicini-rosenbaum-option-roughness",
            ],
            data_requirements=[
                "high-frequency TTWO volatility estimates",
                "dense short-maturity point-in-time TTWO option surfaces",
            ],
            comparison_baseline="validated Heston and finite-factor Bergomi",
            blockers=[
                "available roughness evidence is mainly index-based, not TTWO-specific",
                "non-Markovian calibration and simulation cost has not been benchmarked",
            ],
            reconsideration_gate="Estimate stable TTWO roughness and beat simpler models OOS.",
        ),
        _assessment(
            extension_id="bayesian_filtering",
            label="Bayesian latent-state filtering",
            source_ids=["book-sarkka-svensson-bayesian-filtering-smoothing"],
            data_requirements=[
                "time-indexed state transition and measurement data",
                "identified likelihood with repeated outcomes",
            ],
            comparison_baseline="configured heuristic belief updater and transparent regimes",
            blockers=[
                "no identified TTWO state-space likelihood exists",
                "event outcomes are too sparse for calibration and filter comparison",
            ],
            reconsideration_gate="Pre-register a state-space model and improve OOS calibration.",
        ),
        _assessment(
            extension_id="stochastic_rates_hjm_lmm",
            label="Stochastic rates, HJM and Libor-market models",
            source_ids=["book-andersen-piterbarg-interest-rate-modeling"],
            data_requirements=[
                "point-in-time discount and forward curves",
                "material multi-tenor rate exposure in the target decision",
            ],
            comparison_baseline="provenance-tagged deterministic Treasury curve",
            blockers=[
                "TTWO option ranking sensitivity to stochastic rates is unmeasured",
                "the models target rate-derivative dynamics absent from current scope",
            ],
            reconsideration_gate=(
                "Demonstrate material price/rank changes versus a deterministic curve."
            ),
            out_of_scope=True,
        ),
        _assessment(
            extension_id="essvi_surface",
            label="eSSVI volatility surface",
            source_ids=["paper-mingone-essvi", "paper-cohort-corbetta-martini-laachir-ssvi"],
            data_requirements=["dense cleaned multi-expiry TTWO surfaces across many dates"],
            comparison_baseline="raw SVI with explicit finite-grid arbitrage diagnostics",
            blockers=["raw SVI has not yet failed a real TTWO holdout benchmark"],
            reconsideration_gate="Show raw-SVI failure and eSSVI OOS stability on real surfaces.",
        ),
        _assessment(
            extension_id="learned_regimes",
            label="HMM or machine-learned regimes",
            source_ids=["book-tsay-analysis-financial-time-series"],
            data_requirements=["long point-in-time multi-regime factor history"],
            comparison_baseline="transparent configured regime rules",
            blockers=["regime labels and transition stability are not empirically established"],
            reconsideration_gate=(
                "Improve stable chronological OOS calibration versus simple rules."
            ),
        ),
        _assessment(
            extension_id="hierarchical_event_bayes",
            label="Hierarchical Bayesian event model",
            source_ids=["book-mcelreath-statistical-rethinking"],
            data_requirements=["reviewed repeated event outcomes across a justified population"],
            comparison_baseline="bounded user/configured scenario probability sets",
            blockers=["independent GTA VI-like outcomes are too sparse for partial pooling"],
            reconsideration_gate="Justify the population and validate posterior predictions OOS.",
        ),
        _assessment(
            extension_id="longstaff_schwartz",
            label="Longstaff-Schwartz stopping regression",
            source_ids=["paper-clement-lamberton-protter-lsm"],
            data_requirements=["contracts with measured material checkpoint/FD discrepancy"],
            comparison_baseline="QuantLib finite difference plus checkpoint exit controls",
            blockers=["no material real-contract discrepancy has been demonstrated"],
            reconsideration_gate="Measure a material gap and validate basis/path reuse controls.",
        ),
        _assessment(
            extension_id="higher_order_greeks_aad",
            label="Higher-order Greeks and adjoint differentiation",
            source_ids=["book-nocedal-wright-numerical-optimization"],
            data_requirements=["measured sensitivity-management decision requiring these Greeks"],
            comparison_baseline="current first-order research diagnostics",
            blockers=["read-only small-budget scope has no demonstrated decision need"],
            reconsideration_gate=(
                "Tie stable higher-order sensitivities to a validated decision rule."
            ),
            out_of_scope=True,
        ),
        _assessment(
            extension_id="sobol_qmc_distributed",
            label="Sobol, QMC or distributed Monte Carlo",
            source_ids=["book-glasserman-monte-carlo"],
            data_requirements=["profiled production-sized simulation workloads"],
            comparison_baseline="seeded pseudo-random MC with measured variance reduction",
            blockers=["no reproducible runtime or error bottleneck is established"],
            reconsideration_gate=(
                "Show unbiased reproducible error/cost gain on canonical workloads."
            ),
        ),
        _assessment(
            extension_id="neural_vol_surface",
            label="Neural volatility surface",
            source_ids=["paper-gatheral-jacquier-svi"],
            data_requirements=["large multi-regime arbitrage-reviewed option-surface corpus"],
            comparison_baseline="interpretable constrained SVI/eSSVI",
            blockers=["data volume, transparency and arbitrage guarantees are insufficient"],
            reconsideration_gate=(
                "Beat constrained surfaces OOS with enforceable arbitrage controls."
            ),
            out_of_scope=True,
        ),
    ]
    candidates = sorted(
        item.extension_id
        for item in assessments
        if item.status == "candidate_for_implementation"
    )
    return Phase11ExtensionReview(
        overall_status="NO_ADVANCED_MODEL_IMPLEMENTATION",
        maximum_claim="documentary_gate_only",
        assessments=assessments,
        candidate_for_implementation=candidates,
        integrated_advanced_models=[],
        source_limitations=[
            "Bergomi chapters 1-2 and Andersen-Piterbarg Volume III are absent locally.",
            "The Gatheral book is absent; primary rough-volatility papers were used instead.",
            "Andersen-Piterbarg image-only passages were inspected by bounded OCR.",
            "No source establishes incremental TTWO decision value without TTWO data.",
        ],
    )
