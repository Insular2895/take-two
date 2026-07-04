# risk/ — Gestion du risque

## Rôle
Centraliser les connaissances de risque : mesures (perte max, quantiles), limites de
concentration, risques spécifiques aux options (liquidité, gap, événement, pin risk), garde-fous.

## Ce qui y sera stocké
- Index des règles `R-RISK-NNN` par module (sélection, sizing, maintenance).
- Définitions officielles des mesures de risque utilisées par le scoring.
- Spécification des stress tests exigés avant toute proposition.

## Format attendu
Notes de synthèse + tableaux d'index ; toute mesure définie une seule fois, ici.

## Dépendances
`scoring/`, `simulations/`, `money_management/`, `books/fiches/b_taleb_1997.md`.
