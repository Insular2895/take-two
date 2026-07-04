# volatility/ — Connaissances volatilité

## Rôle
Centraliser IV, HV, IV Rank, IV Percentile, comportement pré/post earnings, IV Crush, méthodes
d'estimation, règles d'entrée/sortie liées à la volatilité.

## Ce qui y sera stocké
- Index des règles `R-VOL-NNN` (source pivot : Sinclair 2013 ; complément : Natenberg).
- Définitions opérationnelles UNIQUES des mesures (ex. « IV Rank 252 jours ») — toute règle du
  repository doit utiliser ces définitions.
- Spécification des données de volatilité requises (Module 3).

## Format attendu
Notes de synthèse + index + définitions. Aucune mesure ambiguë.

## Dépendances
`rules/VOL/`, `greeks/`, `simulations/` (processus de volatilité simulés).
