# Prompt Gemini — Catégorie VOL (v1)

## Objectif
Optimiser l'achat et la vente selon la volatilité.

## Rechercher exclusivement
- volatilité implicite ; volatilité historique ; relation IV/HV ;
- IV Rank ; IV Percentile (définitions opérationnelles + seuils d'usage) ;
- volatilité avant earnings ; IV Crush (amplitude, timing, conditions) ;
- événements de volatilité ; méthodes d'estimation (dont estimateurs de HV) ;
- règles d'entrée ; règles de sortie.

## Ignorer
Débats théoriques sans règle actionnable.

## Format de sortie obligatoire
Format unique. Toute règle de volatilité doit nommer précisément sa mesure
(IV 30j, IV Rank 252j, HV close-to-close 20j, etc.).

## Contrôles
Rejeter les règles dont la mesure de volatilité est ambiguë.
