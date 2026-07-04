# simulations/ — Spécifications des simulations

## Rôle
Documenter TOUTES les simulations que le moteur exécutera : génération de scénarios
(Module 4), simulation des règles de maintenance le long des trajectoires, stress tests.

## Ce qui y sera stocké
- Spécifications de scénarios : variables simulées (prix, volatilité, temps, baisse/hausse/
  stagnation, événements, retard/accélération de thèse), grilles déterministes officielles.
- Contrats de simulation : entrées requises, sorties produites (distributions, quantiles),
  exigences de reproductibilité (graines).
- Protocoles de simulation des règles de maintenance (trailing stops et sorties simulés en chemin).

## Format attendu
Un fichier par spécification, sections : Objectif / Entrées / Procédure / Sorties / Critères de
validité / Références (règles et livres sources).

## Conventions
Aucune constante arbitraire : toute grille ou paramètre cite sa règle source ou son protocole de
calibration dans `validation/`.

## Dépendances
`monte_carlo/`, `decision_engine/03_monte_carlo.md`, `validation/`, `risk/`.
