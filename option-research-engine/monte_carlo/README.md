# monte_carlo/ — Connaissances Monte Carlo

## Rôle
Centraliser les connaissances (règles `MC`) qui gouvernent le simulateur : processus, schémas,
réduction de variance, convergence, reproductibilité.

## Ce qui y sera stocké
- Règles issues de Glasserman, Hull et du repo FMNM (via `rules/MC/`, indexées ici).
- Décisions de modélisation : quel processus par défaut, conditions d'escalade vers Heston/SABR.
- Critères d'arrêt / nombre de trajectoires par convergence (jamais une constante).

## Format attendu
Notes de synthèse pointant vers les règles sources ; aucune affirmation sans règle `R-MC-NNN`.

## Dépendances
`decision_engine/03_monte_carlo.md`, `simulations/`, `benchmarks/`, `books/fiches/b_glasserman_2003.md`.
