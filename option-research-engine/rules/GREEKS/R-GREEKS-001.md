# R-GREEKS-001 — Agréger les Greeks de toute la position

## Titre
Calculer les sensibilités nettes avant d'évaluer une nouvelle jambe.

## Description
Delta, gamma, theta et vega sont additifs entre les jambes d'une position. La sensibilité d'une
option isolée ne décrit donc pas le risque réellement ajouté au portefeuille. Le moteur doit
présenter l'exposition avant et après la transaction envisagée.

## Condition
`nombre_de_jambes >= 1 ET greeks_par_jambe_disponibles = vrai`

## Variables nécessaires
`quantité (contrats signés)`, `multiplicateur (unités/contrat)`, `delta`, `gamma`, `theta
(devise/jour)`, `vega (devise/point de volatilité)`.

## Action
Calculer chaque Greek net comme la somme des sensibilités par jambe multipliées par les quantités et
le multiplicateur ; afficher également la contribution marginale de la transaction proposée.

## Justification
Natenberg indique que les sensibilités sont additives et que leur signe et leur amplitude montrent
comment la position réagit aux changements de marché.

## Risques
Les Greeks sont locaux et dépendent du modèle et de ses entrées. Une somme correcte ne couvre pas
les gaps, changements de volatilité ou non-linéarités loin du point courant.

## Exceptions
Comparer des Greeks calculés avec des conventions ou unités différentes exige une normalisation
préalable.

## Exemple
Cinq options de gamma `2.5` et deux options vendues de gamma `4.0` donnent un gamma net de
`5 × 2.5 - 2 × 4.0 = 4.5`, selon l'exemple corrigé par le calcul.

## Auteur
Sheldon Natenberg.

## Livre
`B-NATENBERG-1994` — *Option Volatility and Pricing*.

## Chapitre
6 — Option Values and Changing Market Conditions.

## Page
PDF p. 134, page imprimée 123.

## Niveau de confiance
4 — auteur de référence, relation chiffrée et directement testable.

## Modules concernés
simulation, scoring, robustesse, maintenance.

## Références croisées
`→ R-GREEKS-002`, `≈ R-GREEKS-003`.

## Tags
greeks, agrégation, risque marginal, portefeuille.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — contexte relu manuellement ; validation quantitative absente.
