# McMillan extraction profile

Use this profile only for McMillan option-strategy material. Preserve edition,
chapter and page. Emphasize architecture construction, payoff boundaries,
assignment/exercise caveats, adjustment sequences, repair/rolling logic,
whole-contract capital recovery and explicit failure modes. Treat historical
examples as historical, not current evidence.

For each extracted item cover: mechanisms; heuristics; testable conditional
rules; formulas; complete strategies; structure, strike and expiration
selection; Delta/moneyness; volatility/liquidity; sizing; profit targets;
stops; time/trailing exits; capital recovery; rolling; adjustments; failure
conditions; exceptions; genuinely stated numeric parameters; missing
parameters requiring calibration; numeric examples; internal contradictions;
and exact references.

Produce Markdown plus strict YAML/JSON. Do not invent thresholds or merge
distinct recipes. Keep LEAPS as a maturity property of a long call/put, not a
separate architecture. Mark every current-market and empirical status
independently. Do not include long copyrighted excerpts.
