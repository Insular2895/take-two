# R-GREEKS-002 — Recalculer la neutralité delta après changement de marché

## Titre
Traiter la neutralité delta comme un état instantané.

## Description
Une position peut être delta-neutre au moment du calcul puis cesser de l'être lorsque le
sous-jacent, le temps ou la volatilité évoluent. Natenberg décrit le hedge comme une série de paris
réévalués. La fréquence optimale de couverture n'est pas donnée par cette règle.

## Condition
`delta_net_précédent ≈ 0 ET au_moins_une_entrée_du_modèle_a_changé = vrai`

## Variables nécessaires
`delta par jambe`, `quantités`, `prix du sous-jacent`, `temps restant`, `IV`, `coûts estimés`,
`tolérance_delta validée`.

## Action
Recalculer le delta net et simuler l'ajustement nécessaire ; alerter si la tolérance validée est
dépassée. Ne pas envoyer automatiquement l'ordre de couverture.

## Justification
Le delta change avec les conditions de marché ; le maintien d'une exposition cible nécessite une
réévaluation.

## Risques
Une couverture trop fréquente peut consommer l'edge en coûts ; une couverture trop lente expose aux
gaps et à la gamma.

## Exceptions
La couverture peut être volontairement non nulle si le mandat de risque l'autorise explicitement.

## Exemple
Dans l'exemple du livre, un delta d'option passant de `57` à `62` transforme un hedge initialement
neutre en exposition nette positive.

## Auteur
Sheldon Natenberg.

## Livre
`B-NATENBERG-1994` — *Option Volatility and Pricing*.

## Chapitre
5 — Using an Option's Theoretical Value.

## Page
PDF p. 94, page imprimée 83.

## Niveau de confiance
4 — mécanisme quantifiable ; fréquence et seuil restent à valider.

## Modules concernés
simulation, robustesse, alertes, maintenance.

## Références croisées
`→ R-GREEKS-001`, `≈ R-GREEKS-003`, `≠ C-003`.

## Tags
delta, hedge, rebalancement, gamma.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — action limitée au recalcul et à la simulation.
- 2026-07-05 — NORMALISÉE — revue visuelle des figures 6-6 à 6-9, pages imprimées 104 et 107.
- 2026-07-06 — NORMALISÉE — figures 6-10 et 6-11, page imprimée 108 ; dépendance du gamma à
  l'IV et du delta au temps confirmée qualitativement.
- 2026-07-06 — NORMALISÉE — figures 6-12 à 6-14, pages imprimées 109–110 ; dépendance du delta
  au temps et à l'IV confirmée pour calls et puts.
- 2026-07-06 — NORMALISÉE — chapitre 9, pages imprimées 193–195 ; ajustement delta via
  sous-jacent séparé des ajustements par options, qui modifient aussi gamma, theta et vega.
