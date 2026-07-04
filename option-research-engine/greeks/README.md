# greeks/ — Connaissances Greeks

## Rôle
Centraliser tout ce qui transforme Delta, Gamma, Theta, Vega en décisions : seuils, relations,
dominances, surveillance, critères de vente et de rolling.

## Ce qui y sera stocké
- Index des règles `R-GREEKS-NNN` (sources principales : Natenberg, Passarelli, Taleb, Hull).
- Définitions normalisées des Greeks (unités, plages) valables pour tout le repository.
- Spécification de la surveillance : fréquences et déclencheurs (sourcés).

## Format attendu
Notes de synthèse + index ; les seuils vivent dans les règles, pas ici.

## Dépendances
`rules/GREEKS/`, `docs/06_moteur_maintenance.md`, `volatility/` (interactions Vega×IV).
