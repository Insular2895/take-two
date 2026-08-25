# Natenberg extraction profile

Use this profile only for *Option Volatility and Pricing*. Preserve exact
chapter/page provenance. Emphasize volatility assumptions, theoretical value,
Greeks, skew/term structure, spreads, calendars, butterflies, risk and
position management. Distinguish mathematical identities from pedagogical
examples and trading heuristics.

For each extracted item cover: mechanisms; heuristics; testable conditional
rules; formulas; complete strategies; structure, strike and expiration
selection; Delta/moneyness; volatility/liquidity; sizing; profit targets;
stops; time/trailing exits; capital recovery; rolling; adjustments; failure
conditions; exceptions; genuinely stated numeric parameters; missing
parameters requiring calibration; numeric examples; internal contradictions;
and exact references.

Produce one readable Markdown card and one strict YAML/JSON object per item.
Produce `StrategyRecipe` only when a complete structure is identifiable.
Never convert qualitative language into a number. Mark absent information
`null`, `unknown`, `calibration_required`, or `insufficient_data`. Do not infer
current profitability. Do not include long copyrighted excerpts.
