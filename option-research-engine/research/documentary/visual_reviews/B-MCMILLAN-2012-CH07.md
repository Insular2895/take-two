# Revue visuelle — B-MCMILLAN-2012 — Chapitre 7

Source : Lawrence G. McMillan, *Options as a Strategic Investment*, 5e édition.

Chapitre : 7 — Bull Spreads.

Statut : `in_progress`

Date de revue : 2026-07-06.

Périmètre reçu : chapitre complet, pages imprimées `172–185`.

Les images ne sont pas versionnées. Cette fiche conserve les mécanismes, exemples et limites
contrôlés visuellement. Aucune règle n'est active pour trading ou exécution IBKR.

## Construction et payoff — pages 172–174, tableau 7-1 et figure 7-1

Le bull call spread consiste à :

- acheter un call au strike inférieur ;
- vendre un call de même échéance au strike supérieur.

Il est établi pour un débit, car le call acheté vaut plus cher. Son risque et son profit sont
limités.

Formules données :

- break-even = strike inférieur + débit net ;
- profit maximal = écart entre strikes − débit net ;
- perte maximale = débit net, commissions incluses dans l'analyse réelle.

Exemple :

- achat du call octobre `30` à `3` ;
- vente du call octobre `35` à `1` ;
- débit net `2` ;
- break-even `32` ;
- profit maximal `3`, atteint à partir de `35`.

McMillan le présente comme une position haussière mais couverte : au-dessus du strike haut, le call
vendu plafonne le gain du call acheté.

## Degrés d'agressivité — pages 175–176

- Spread agressif : sous-jacent proche du strike inférieur ; rendement potentiel élevé mais
  probabilité de perte supérieure.
- Spread extrêmement agressif : deux calls OTM ; faible coût, mais risque élevé de perte totale du
  débit.
- Spread moins agressif : deux calls ITM ; probabilité plus forte d'atteindre le gain maximal, mais
  rendement potentiel plus faible.

McMillan avertit que les spreads OTM ne doivent mobiliser qu'une très petite part des fonds
spéculatifs.

## Classement des bull spreads — page 176

Classer uniquement par profit maximal à l'expiration est jugé trompeur. Le classement devrait
incorporer :

- volatilité du sous-jacent ;
- évolution attendue du spread avant l'expiration ;
- temps restant ;
- rendement attendu ;
- commissions.

Un filtre simplifié peut comparer le mouvement attendu du sous-jacent à sa valeur temps ATM, mais
McMillan le présente comme une approximation inférieure à une analyse complète.

## Spread contre call sec — pages 177–178, tableau 7-2

Le call sec tend à être meilleur lorsque :

- le mouvement attendu est rapide ;
- la hausse est forte ;
- l'horizon est court.

Le bull spread tend à être meilleur lorsque :

- la hausse est lente ou modérée ;
- le sous-jacent reste relativement stable ;
- l'analyse va jusqu'à l'expiration ;
- la réduction du capital à risque importe davantage que l'upside illimité.

Plus le mouvement met du temps à se produire, plus l'avantage relatif du spread augmente. Le spread
supporte cependant davantage de commissions.

## Follow-Up Action — pages 179–180

Le spread possède déjà un risque borné, mais peut être fermé avant l'expiration :

- si le sous-jacent monte suffisamment et que la valeur temps du call short disparaît ;
- pour limiter une perte si le sous-jacent baisse.

Principes d'exécution :

- fermer le spread comme une transaction unique ;
- le crédit maximal théorique ne peut pas dépasser l'écart entre strikes ;
- McMillan recommande généralement au public de liquider plutôt que d'exercer ;
- ne pas sortir jambe par jambe en espérant optimiser chaque côté : le risque augmente.

Une exception prudente consiste à racheter le call short devenu presque sans valeur, mais sans
continuer ensuite à « leg out » de la position.

## Autres usages — pages 180–185, tableaux 7-3 et 7-4, figure 7-2

### Réduction du break-even d'une action

Exemple :

- action achetée à `48`, désormais à `42` ;
- achat d'un call octobre `40` à `4` ;
- vente de deux calls octobre `45` à `2`.

La combinaison crée :

- un bull spread `40/45` ;
- un covered call sur l'action.

Elle abaisse le break-even global d'environ `48` à `44`, sans coût initial hors commissions, mais
plafonne le profit au-dessus de `45`.

### Substitut au covered write

Un call profondément ITM avec très peu de valeur temps peut remplacer économiquement l'action dans
une structure de covered write :

- capital immobilisé inférieur ;
- risque en dollars inférieur ;
- profit maximal et break-even comparables dans l'exemple ;
- revenu d'intérêt possible sur le capital non immobilisé.

La réplication reste imparfaite : le call ne verse pas le dividende et dépend de la disponibilité
d'un contrat suffisamment ITM.

## Impact projet

Le moteur doit :

- calculer débit, break-even, profit et perte maximaux après coûts ;
- classer le spread selon le scénario et l'horizon, pas seulement son payoff terminal ;
- comparer systématiquement call sec et spread ;
- contrôler liquidité, commissions et exécution simultanée ;
- interdire toute sortie jambe par jambe non prévue par une politique explicite ;
- signaler le plafonnement de l'upside et les effets de marge.
