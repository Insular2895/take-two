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

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_donnees_contrat_live`.

Le principe reste actuel : les Greeks doivent être agrégés au niveau position, portefeuille et
transaction marginale. La partie à ne pas reprendre aveuglément depuis les livres est la mécanique
contractuelle : le multiplicateur standard de nombreuses options actions US est souvent 100, mais
il peut changer après corporate action ou contrat ajusté. Le moteur doit donc lire le
`multiplier`, le `deliverable`, le `tradingClass`, le `localSymbol` et le `conId` depuis OCC/IBKR,
et conserver la convention source des Greeks avant normalisation.

Contrôle obligatoire avant scoring : refuser l'agrégation si une jambe n'a pas de multiplicateur,
devise, modèle, timestamp, convention de vega/theta ou statut de contrat ajusté.

Sources 2026 : OCC equity options product specifications ; OCC ODD ; IBKR contract details /
option chain API.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — contexte relu manuellement ; validation quantitative absente.
- 2026-07-06 — NORMALISÉE — figures 6-20 à 6-23, pages imprimées 116–119 ; dimensions vega,
  rho, maturité et type de sous-jacent contrôlées visuellement.
- 2026-07-06 — NORMALISÉE — figures 6-24 et 6-25, pages imprimées 121–122 ; tableaux
  numériques par strike et maturité transcrits partiellement, convention theta à résoudre.
- 2026-07-06 — NORMALISÉE — chapitre 5, pages imprimées 82–93 ; delta position, hedge
  dynamique et cash flows d'ajustement documentés dans deux exemples.
