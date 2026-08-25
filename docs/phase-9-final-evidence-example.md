# Phase 9 example — final evidence sidecar

```python
grade = calculate_decision_evidence_grade(
    [
        ComponentEvidenceClaim(
            component_id="pricing",
            implemented=True,
            tests_passed=True,
            numerical_validation_passed=True,
            source_ids=["book-bjork-arbitrage-theory"],
        ),
        ComponentEvidenceClaim(
            component_id="event_probabilities",
            implemented=True,
            tests_passed=True,
            blockers=["No real TTWO calibration dataset."],
        ),
    ]
)
assert grade.overall_grade == EvidenceGrade.TESTED
```

A `FinalDecisionEvidenceReport` then requires estimates, probability intervals, assumptions,
favorable and failure scenarios, model risks, data limits, exact ranking reasons, sources and exact
`NO_TRADE` reasons when applicable. Its Markdown and HTML views contain the same sections.

The committed test example is deliberately synthetic: expected P&L is shown with a model range,
the target probability with a configured-belief sensitivity range, and `NO_TRADE` wins because
event probabilities lack empirical validation. The output is static, has no script or network
asset, requires a human and preserves `order_capability=forbidden`.
