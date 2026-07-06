# R-OPTIONS-001 — Comparer l'edge théorique à l'exécutabilité

## Titre
Rejeter une structure dont l'avantage disparaît à l'exécution.

## Description
Une structure théoriquement supérieure peut exiger davantage de jambes, de taille ou de coûts.
Natenberg montre qu'un butterfly peut dominer théoriquement tout en étant difficile à exécuter aux
prix cibles. La comparaison doit donc utiliser des cotations et tailles réellement disponibles.

## Condition
`nombre_de_jambes >= 2 ET edge_théorique > 0`

## Variables nécessaires
`bid`, `ask`, `taille bid/ask`, `volume`, `open interest`, `nombre de jambes`, `quantité`,
`commissions`, `slippage`, `edge théorique`.

## Action
Calculer l'edge net exécutable de la structure complète et de ses alternatives plus simples ;
rejeter la structure si la liquidité ne supporte pas la taille ou si l'edge net devient négatif.

## Justification
Le bid-ask cumulé, le risque de legging, la taille requise et les commissions peuvent annuler
l'avantage théorique.

## Risques
Les cotations affichées peuvent ne pas être exécutables simultanément et l'impact augmente avec la
taille.

## Exceptions
Une exécution combinée garantie à un prix limite peut réduire, sans supprimer, le risque
d'exécution.

## Exemple
Le livre compare un butterfly trois côtés de taille `70 × 140 × 70` à des spreads deux côtés et
signale que la liquidité peut empêcher l'exécution requise.

## Auteur
Sheldon Natenberg.

## Livre
`B-NATENBERG-1994` — *Option Volatility and Pricing*.

## Chapitre
9 — Risk Considerations.

## Page
PDF p. 191, page imprimée 181.

## Niveau de confiance
4 — mécanisme concret, observable et testable avec un carnet actuel.

## Modules concernés
sélection, sizing, simulation, scoring, robustesse.

## Références croisées
`≈ C-004`, `≈ C-005`.

## Tags
liquidité, spread, bid-ask, exécution, edge net.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — contexte complet relu manuellement.
- 2026-07-06 — NORMALISÉE — chapitre 8 de Natenberg contrôlé visuellement ; payoffs,
  sensibilités et anciens champs d'ordres multi-jambes documentés.
- 2026-07-06 — NORMALISÉE — figure 8-20 complétée, pages imprimées 165–166 ; butterflies et
  time spreads vérifiés par leurs jambes et Greeks agrégés.
- 2026-07-06 — NORMALISÉE — chapitre 9, pages imprimées 174–178 et figure 9-6 ; l'edge est comparé
  après ajustement de taille, puis stressé en volatilité et sous-jacent avant toute préférence.
