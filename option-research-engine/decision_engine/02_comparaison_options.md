# Comparaison des options

## 1. Variables de comparaison

Par contrat : strike, échéance, bid/ask, spread relatif, volume, open interest, Delta, Gamma,
Theta, Vega, IV (et sa position : IV Rank / IV Percentile). Par structure : coût total, perte
maximale, exposition nette (Greeks agrégés), point mort, sensibilité au temps et à la volatilité.

## 2. Principes de comparaison

- Comparaison **à budget identique** : toute structure candidate est normalisée sur le budget fourni.
- Comparaison **multi-scénarios** : la valeur d'une structure n'est jamais un point, c'est une
  distribution (issue de `03_monte_carlo.md`).
- Comparaison **explicable** : chaque écart de score entre deux structures doit être décomposable
  (espérance, probabilité, risque, liquidité, coût, robustesse).

## 3. Coûts intégrés

Spread bid/ask, commissions, slippage estimé, coût des rollings anticipés. Les méthodes
d'estimation proviennent de la littérature (`rules/TRADSYS/`, `research/benchmarks/`).
