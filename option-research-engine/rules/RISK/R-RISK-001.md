# R-RISK-001 — Évaluer un signal après contraintes et coûts

## Titre
Séparer edge brut, capacité exploitable et valeur nette.

## Description
Grinold et Kahn relient la performance attendue au skill et au nombre de paris réellement
indépendants. Ils montrent aussi que contraintes et turnover réduisent la valeur ajoutée et que le
trading est un problème d'optimisation distinct. Une opportunité brute ne vaut donc pas performance
nette.

## Condition
`signal_brut_disponible = vrai`

## Variables nécessaires
`edge brut`, `corrélation entre signaux`, `contraintes`, `turnover`, `commissions`, `bid-ask`,
`impact`, `risque actif`, `edge net`.

## Action
Calculer l'edge après contraintes et coûts, puis rejeter toute candidate dont l'edge net n'est pas
positif et robuste dans les scénarios retenus.

## Justification
Les contraintes réduisent l'information exploitable et le processus d'exécution consomme une partie
de la valeur ajoutée théorique.

## Risques
Sous-estimation des corrélations, de l'impact ou du turnover ; transposition imparfaite d'un cadre
actions institutionnel aux options.

## Exceptions
Les formules et seuils du livre ne doivent pas être transposés aux options sans calibration.

## Exemple
Le livre donne comme règle empirique qu'une réduction de moitié du turnover peut conserver au moins
trois quarts de la valeur ajoutée ; ce ratio reste un benchmark à tester.

## Auteur
Richard C. Grinold et Ronald N. Kahn.

## Livre
`B-GRINOLD-KAHN-1999` — *Active Portfolio Management*, 2e édition.

## Chapitre
6 — The Fundamental Law of Active Management ; 16 — Transactions Costs, Turnover, and Trading.

## Page
PDF p. 168 et 473, pages imprimées 161 et 469.

## Niveau de confiance
3 — cadre quantitatif solide, mais transposition aux options à valider.

## Modules concernés
sizing, simulation, scoring, robustesse.

## Références croisées
`→ R-OPTIONS-001`, `→ R-GREEKS-003`, `≈ C-004`.

## Tags
coûts, contraintes, turnover, information ratio, edge net.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_contraintes_broker_et_stress`.

Le principe reste actuel : l'edge net doit être évalué après contraintes et coûts. En 2026, cela
inclut marge, permissions, borrow, locate, Regulation SHO/Rule 201, position limits, liquidité,
taxes possibles, turnover, commissions, slippage, capacité de liquidation, assignment et corporate
actions. Les stratégies à risque non borné doivent rester bloquées sans stress test et validation
humaine.

Contrôle obligatoire avant scoring : stress gaps/halts/IV crush/spread widening/assignment,
`max_size`, permissions broker, marge pré-trade, disponibilité borrow, et statut
`human_required` pour tout risque non borné ou short vol.

Sources 2026 : IBKR margin/commissions/short availability ; SEC Regulation SHO Rule 201 ; OCC ODD.

## Historique
- 2026-07-05 — DÉDUPLIQUÉE — fusion de candidates sur information et exécution.
- 2026-07-05 — NORMALISÉE — seuil empirique conservé comme benchmark non actif.
- 2026-07-06 — NORMALISÉE — chapitre 8 de Natenberg ; coûts multi-jambes, liquidité et risque
  de legging ajoutés aux exigences documentaires.
