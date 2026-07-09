# Revue visuelle — B-PASSARELLI-2012 — Chapitre 13

Source : Dan Passarelli, *Trading Option Greeks*, 2e édition.

Chapitre : 13 — Delta-Neutral Trading: Trading Realized Volatility.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
valeurs utiles et limites contrôlées visuellement. Les conclusions restent documentaires : aucune
règle n'est active pour trading ou exécution IBKR.

## Gamma scalping — page imprimée 248

Passarelli présente le gamma scalping comme une technique de trading de volatilité réalisée, pas
comme une stratégie directionnelle.

### Mécanisme

- Une position long gamma delta-neutre ne reste pas delta-neutre quand le sous-jacent bouge.
- Quand le sous-jacent monte, le delta de la position devient positif.
- Quand le sous-jacent baisse, le delta de la position devient négatif.
- Le trader long gamma cherche à verrouiller les gains de delta en vendant le sous-jacent après une
  hausse et en l'achetant après une baisse.
- Le profit de scalping doit couvrir le theta, qui est le coût quotidien du trade.

### Exemple initial

Position delta-neutre :

- achat de `20` calls strike `40`, delta `50` ;
- vente de `1,000` actions à `$40`.

Équilibre initial :

- calls : `+1,000 deltas` ;
- actions short : `-1,000 deltas`.

## Figure 13.1 — 20-lot delta-neutral long call — page imprimée 249

Position :

- long `20` calls strike `40` ;
- short `1,000` shares à `$40`.

Greeks affichés :

| Greek | Valeur |
|---|---:|
| Delta | 0 |
| Gamma | +2.80 |
| Theta | -0.50 |
| Vega | +1.15 |

Interprétation :

- Long gamma ;
- theta négatif ;
- vega positif ;
- l'objectif est de produire assez de profits de scalping pour couvrir le theta.

## Exemple long gamma — jours 1 à 7, pages imprimées 249–253

### Jour 1 — forte oscillation

Le sous-jacent monte de `$40` à `$42`, puis revient à `$40`.

À `$42`, la position a environ `+5.60` deltas, soit `+560` actions. Le trader vend `560` actions à
`$42`. Quand le sous-jacent revient à `$40`, la position devient short delta et le trader rachète
`560` actions à `$40`.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Vendu `560` actions à `$42` |
| Racheté `560` actions à `$40` |
| `560 × $2` | `$1,120` |
| `-1 day theta × $50` | `($50)` |
| Profit net | `$1,070` |

Observation :

- Une journée très volatile peut largement couvrir le theta.
- Si le mouvement avait été plus petit, le profit de scalping aurait pu être insuffisant.

### Jour 2 — faible mouvement

Le sous-jacent baisse de `$0.40`, puis revient à `$40`.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Achat `112` actions à `$39.60` |
| Vente `112` actions à `$40.00` |
| Profit brut | `$45` |
| `-1 day theta × $50` | `($50)` |
| Résultat net | `($5)` |

Observation :

- Le gamma scalping peut perdre même si le hedge est correct, lorsque le mouvement réalisé ne couvre
  pas le theta.

### Jour 3 — marché directionnel favorable au long gamma

Le sous-jacent monte par étapes de `$40` à `$42`. Le trader vend `140` actions à chaque tranche de
`$0.50`.

Calcul affiché :

- quatre ventes de `140` actions ;
- chaque segment produit `140 × $0.50 / 2 = $35` ;
- profit gamma total : `$140` ;
- theta : `($50)` ;
- profit net : `$90`.

Observation :

- Le long gamma peut gagner même dans un mouvement directionnel si les deltas sont couverts par
  étapes.
- Le calcul utilise l'average delta créé sur chaque tranche de prix.

### Jour 4 — gap favorable

Le sous-jacent ouvre `$4` plus bas. Le trader rachète `1,120` actions à `$38`.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Achat `1,120` actions à `$38` |
| `1,120 × $4 / 2` | `$2,240` |
| `-1 day theta × $50` | `($50)` |
| Profit net | `$2,190` |

Observation :

- Le gap favorable est le plus gros contributeur de la semaine.
- Une partie du profit vient du fait que les deltas n'étaient pas couverts trop tôt.

### Jours 5 et 6 — week-end

Le marché est fermé, mais le theta continue :

- `-2 days theta × $50 = $100 loss`.

Observation :

- Week-ends et jours fériés sont des obstacles importants pour les positions long gamma.

### Jour 7 — journée calme

Le sous-jacent monte de `$0.25`.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Vente `70` actions à `$38.25` |
| `70 × $0.25 / 2` | `$9` |
| `-1 day theta × $50` | `($50)` |
| Résultat net | `($41)` |

Observation :

- Le mouvement réalisé est trop faible pour couvrir le theta.

## Art and science — page imprimée 253

Passarelli insiste sur le caractère non mécanique du gamma scalping.

### Points contrôlés

- Le trader long gamma veut idéalement vendre les plus hauts et acheter les plus bas, mais cela
  arrive rarement parfaitement.
- Couvrir trop tôt peut réduire les gains.
- Couvrir trop tard peut rater des opportunités ou laisser un risque directionnel.
- Les méthodes de couverture peuvent être fondées sur :
  - un écart-type quotidien ;
  - un pourcentage fixe du prix ;
  - une valeur nominale fixe ;
  - une heure de la journée ;
  - le feeling discrétionnaire du trader.

### Impact projet

Le futur moteur ne doit pas simuler une seule politique de hedge. Il doit tester plusieurs règles de
rebalancement :

- seuil de delta ;
- seuil de mouvement en prix ;
- seuil en écart-type ;
- fréquence temporelle ;
- hedge partiel vs hedge total.

## Gamma, theta and volatility — pages imprimées 253–254

Passarelli relie directement la rentabilité du gamma scalping au ratio gamma/theta et à la
volatilité réalisée.

### Points contrôlés

- Plus l'IV est élevée, plus le theta des options ATM est élevé dans l'exemple.
- Une action plus volatile doit bouger davantage pour couvrir un theta plus élevé.
- Dans l'exemple, `0.50` de theta permet d'acheter `2.80` de gamma à `25 %` IV.
- Si l'IV était `50 %`, le theta serait environ deux fois plus élevé et le gamma plus faible.
- À `50 %`, il pourrait acheter environ `1.40` gamma pour `0.90` theta.
- Le gamma devient donc plus cher du point de vue theta quand l'IV monte.

### Gamma hedging — page imprimée 254

Passarelli utilise l'IV de `25 %` comme benchmark pour juger la profitabilité possible du gamma
trading :

- si la volatilité réalisée du sous-jacent est sous `25 %`, il devient difficile de gagner en étant
  long gamma ;
- si elle est au-dessus de `25 %`, le trade devient plus facile ;
- mais `RV >= IV` ne garantit pas le succès : le résultat dépend aussi de la qualité du scalping.

### Impact projet

Le moteur doit comparer :

- IV payée ;
- volatilité réalisée estimée ou simulée ;
- gamma acheté ;
- theta payé ;
- politique de hedge ;
- coûts d'exécution ;
- gaps et week-ends.

Il ne doit pas transformer `RV > IV` en signal automatique.

## Figure 13.2 — 20-lot delta-neutral short call — page imprimée 255

Position :

- short `20` calls strike `40` ;
- long `1,000` shares à `$40`.

Greeks affichés :

| Greek | Valeur |
|---|---:|
| Delta | 0 |
| Gamma | -2.80 |
| Theta | +0.50 |
| Vega | -1.15 |

Interprétation :

- Short gamma ;
- theta positif ;
- vega négatif ;
- position baissière sur la volatilité réalisée.

## Exemple short gamma — pages imprimées 255–259

### Principe

Le short gamma gagne le theta si le marché reste calme, mais les grands mouvements créent des deltas
adverses qui peuvent grossir rapidement.

### Jour 1

Le sous-jacent monte de `$40` à `$42`, puis revient à `$40`.

Dans le scénario idéal décrit, Mary ne couvre pas à `$42` et le retour à `$40` rend la position
delta-neutre sans perte de hedge.

Résultat affiché :

- `1 day theta × $50 = $50 profit`.

### Jour 2

Petit mouvement de `$0.40`, jugé normal. Mary ne hedge pas.

Résultat affiché :

- `1 day theta × $50 = $50 profit`.

### Jour 3

Le sous-jacent monte progressivement. Mary achète `280` actions à `$41`, puis `280` actions à `$42`
pour réduire le risque de delta adverse.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Achat `280` actions à `$41` | `($140)` |
| Achat `280` actions à `$42` | `($140)` |
| Pertes gamma | `($280)` |
| Theta | `$50` |
| Résultat net | `($230)` |

Observation :

- Couvrir une position short gamma peut cristalliser des pertes, mais ne pas couvrir peut être pire
  si le mouvement continue.

### Jour 4 — gap défavorable

Le sous-jacent ouvre `$4` plus bas. Mary vend `560` actions à `$38` et garde volontairement une
partie du delta non couverte.

Calcul affiché :

| Élément | Montant |
|---|---:|
| Vente `560` actions à `$38` | `($1,120)` |
| Deltas longs restants issus du gamma négatif | `($1,120)` |
| Theta | `$50` |
| Résultat net | `($2,190)` |

Observation :

- Le jour que le long gamma adore est celui que le short gamma redoute.
- Couvrir totalement aurait rendu la position flat mais aurait aussi accepté le risque d'un rebond
  ou d'une poursuite du mouvement.

### Jours 5 et 6

Week-end :

- `2 days theta × $50 = $100 profit`.

### Jour 7

Le sous-jacent monte de `$0.25`. Mary reste encore partiellement exposée.

Décomposition affichée :

| Élément | Montant |
|---|---:|
| Long `560` deltas : `560 × $0.25` | `$140` |
| `-70` deltas créés par gamma : `70 × $0.25 / 2` | `($9)` |
| Theta | `$50` |
| Résultat net | `$181` |

Observation :

- Une exposition directionnelle résiduelle peut aider ou nuire ; elle n'est pas un profit pur de
  volatilité.

## Conclusions Passarelli — page imprimée 259

### Points contrôlés

- Les deux traders utilisent la même semaine et des positions opposées.
- Les résultats ne sont pas strictement symétriques car chacun hedge différemment.
- Le trading d'options n'est pas un jeu à somme nulle une fois les politiques de hedge prises en
  compte.
- Les stratégies delta-neutres short options fonctionnent mieux dans des environnements de faible
  volatilité.
- Les petits mouvements sont acceptables ; les gros mouvements peuvent être destructeurs.
- Les short-gamma traders disposent de plusieurs techniques pour couvrir les deltas, mais il n'existe
  pas de méthode unique.
- L'écart-type quotidien dérivé de l'IV est une mesure courante pour décider où entrer des hedges.
- Le trader doit trouver ce qui fonctionne pour lui, pour son style et pour le sous-jacent.

## Smileys and frowns — pages imprimées 260–263

Passarelli introduit les diagrammes P&L des positions delta-neutres :

- le P&L global de la position compte plus que le P&L isolé des calls ou des actions ;
- gamma et delta doivent être surveillés ensemble ;
- une position positive gamma produit un profil `smiley` : les coins montent lorsque le sous-jacent
  s'éloigne du centre ;
- la figure 13.3 illustre une position delta-neutre positive gamma.

### Figure 13.3 — positive-gamma delta-neutral position

Le profil P&L a une forme de sourire :

- le centre est proche de zéro à l'initiation ;
- les extrémités montent lorsque le sous-jacent s'éloigne du centre ;
- cela représente le fait que le profit augmente lorsque les deltas changent favorablement dans un
  mouvement de prix suffisamment large.

### Figure 13.4 — effect of time on P&L

La figure montre l'effet du passage du temps sur un trade long gamma :

- le centre du graphe descend en territoire négatif avec le temps ;
- cette baisse représente le theta decay ;
- malgré ce coût, un mouvement suffisamment grand dans un sens ou l'autre peut encore rendre la
  position profitable ;
- à expiration, le payoff prend une forme plus rigide/kinked.

Passarelli précise aussi que la volatilité déplace le payoff verticalement :

- hausse d'IV : les options valent plus à chaque prix du sous-jacent ;
- baisse d'IV : les options valent moins, toutes choses égales par ailleurs.

### Figure 13.5 — short-gamma frown

Le short gamma produit une forme inverse :

- le point le plus haut est au centre ;
- le profit se détériore lorsque le sous-jacent monte ou baisse ;
- le graphe ne montre pas directement le passage du temps ni la volatilité.

### Figure 13.6 — effect of time on the short-gamma frown

Le temps aide le short gamma :

- le theta positif augmente le profit potentiel au centre ;
- le pic de profit se concentre autour du strike à expiration ;
- une hausse d'IV réduit la profitabilité à chaque prix du sous-jacent ;
- une baisse d'IV augmente la profitabilité à chaque prix du sous-jacent.

### Conclusion du chapitre — page imprimée 263

Les diagrammes smiley/frown ne montrent que le payoff en fonction du mouvement du sous-jacent. Ils
sont limités car les stratégies delta-neutres sont aussi influencées par :

- le temps ;
- l'IV ;
- la politique de couverture ;
- la volatilité réalisée.

Passarelli conclut que les stratégies du chapitre sont les mêmes familles de stratégies que dans le
chapitre précédent ; la différence est la philosophie : acheter ou vendre de la volatilité réalisée.
IV et RV vont ensemble dans l'analyse.

## Conclusions provisoires pour Take Two

1. Le gamma scalping est un trade de volatilité réalisée, pas une simple lecture IV/RV.
2. Le long gamma gagne quand les mouvements capturés par le hedge couvrent theta et coûts.
3. Le short gamma gagne quand les mouvements restent assez faibles pour que theta domine.
4. Le week-end et les jours fériés pèsent contre le long gamma via theta.
5. Les gaps peuvent dominer toute la semaine de P&L.
6. La politique de hedge change fortement le résultat, donc elle doit être paramétrable.
7. `RV > IV` aide le long gamma mais ne garantit pas un profit.
8. `RV < IV` aide le short gamma mais ne garantit pas un profit.
9. Le futur moteur doit simuler long et short gamma avec plusieurs politiques de hedge, coûts,
   slippage, gaps et theta calendrier.
10. Les résultats doivent être agrégés au niveau de la position complète, pas jambe par jambe.
11. Les visualisations P&L doivent permettre de faire varier temps et IV, pas seulement le prix du
    sous-jacent.
