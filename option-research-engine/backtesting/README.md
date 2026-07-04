# backtesting/ — Méthodologie de backtesting

## Rôle
Centraliser la méthodologie de test historique et de robustesse : protocoles, biais, corrections,
spécificités des options (chaînes historiques, chemins dépendants des règles de maintenance).

## Ce qui y sera stocké
- Index des règles de méthode (sources : Pardo, Aronson, ML4T).
- Exigences de données pour backtester des options (qualité des chaînes, survivorship, IV historique).
- Limites documentées : ce que le backtest NE peut pas prouver (→ rôle de Monte Carlo).

## Format attendu
Notes de synthèse + index + checklists renvoyant aux protocoles de `validation/`.

## Dépendances
`validation/`, `rules/TRADSYS/`, `rules/PROBA/`, `research/benchmarks/machine-learning-for-trading.md`.
