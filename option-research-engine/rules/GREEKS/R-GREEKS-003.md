# R-GREEKS-003 — Évaluer le long gamma net du theta et des coûts

## Titre
Comparer les gains de rebalancement au theta et aux coûts.

## Description
Passarelli décrit le gamma scalping comme une activité de couverture répétée où le trader vend le
sous-jacent après une hausse et l'achète après une baisse. Le résultat réalisé doit couvrir le theta.
Le succès dépend aussi de la qualité et de la fréquence des couvertures.

## Condition
`gamma_net > 0 ET stratégie_delta_hedgée = vrai`

## Variables nécessaires
`gamma net`, `theta quotidien`, `delta net`, `P&L des hedges`, `commissions`, `slippage`,
`volatilité réalisée`, `IV`, `fréquence de hedge`.

## Action
Mesurer `P&L_hedges - theta - coûts` sur l'horizon et stresser plusieurs politiques de couverture ;
ne pas qualifier la stratégie de rentable sur la seule comparaison IV/RV.

## Justification
Le gamma crée des occasions de rebalancement, mais le theta constitue un coût quotidien et les
hedges ne capturent pas automatiquement tous les mouvements.

## Risques
Gaps, coûts, mauvais timing de couverture, variation de gamma/IV et pertes liées à une volatilité
réalisée insuffisante.

## Exceptions
Une position non couverte ou volontairement directionnelle ne relève pas de cette mesure seule.

## Exemple
Le livre présente une position delta-neutre de vingt calls et fixe comme objectif quotidien que les
profits du gamma couvrent le theta.

## Auteur
Dan Passarelli.

## Livre
`B-PASSARELLI-2012` — *Trading Option Greeks*.

## Chapitre
13 — Trading Realized Volatility.

## Page
PDF p. 272-278, pages imprimées 248-254.

## Niveau de confiance
4 — mécanisme chiffrable ; politique de hedge et coûts à valider quantitativement.

## Modules concernés
simulation, scoring, robustesse, maintenance.

## Références croisées
`→ R-GREEKS-001`, `→ R-GREEKS-002`, `→ R-VOL-001`, `≠ C-002`.

## Tags
gamma, theta, delta hedge, volatilité réalisée, coûts.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur les pages PDF.
- 2026-07-05 — NORMALISÉE — contexte relu ; raccourci `IV > RV donc vendre` rejeté.
- 2026-07-05 — NORMALISÉE — figure 6-9 de Natenberg, page imprimée 107, utilisée comme
  confirmation qualitative du risque gamma proche de l'échéance.
- 2026-07-06 — NORMALISÉE — figure 6-10 de Natenberg, page imprimée 108 ; le gamma dépend de
  la volatilité différemment selon la moneyness.
- 2026-07-06 — NORMALISÉE — figures 6-15 à 6-17, pages imprimées 112–113 ; accélération du
  theta ATM et comportement distinct des options non-ATM confirmés visuellement.
- 2026-07-06 — NORMALISÉE — figures 6-20 et 6-21, pages imprimées 116–117 ; dépendance du vega
  au temps, à l'IV et à la moneyness contrôlée visuellement.
- 2026-07-06 — NORMALISÉE — figure 6-25, page imprimée 122 ; baisse du gamma et hausse du vega
  avec la maturité vérifiées au strike 75.
- 2026-07-06 — NORMALISÉE — figures 8-13, 8-14 et 8-19 ; opposition gamma/theta et cas
  particulier des time spreads contrôlés visuellement.
