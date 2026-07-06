# Revue visuelle — B-NATENBERG-1994 — Chapitre 9

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Chapitre : 9 — Risk Considerations.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
valeurs utiles et limites contrôlées visuellement. Les conclusions restent documentaires : aucune
règle n'est active pour trading ou exécution IBKR.

## Table d'évaluation initiale — page 174, figure 9-1

### Hypothèses visibles

Deux marchés futures sont comparés :

- May Futures : `49.50`, temps à expiration `56 jours`, volatilité modèle `15 %`, taux `8 %`.
- July Futures : `50.11`, temps à expiration `112 jours`, volatilité modèle `15 %`, taux `8 %`.

La figure donne pour calls et puts :

- prix de marché ;
- valeur théorique ;
- delta ;
- gamma ;
- theta ;
- vega ;
- volatilité implicite.

### Points contrôlés

Pour les strikes proches du sous-jacent, les options de mai ont des gammas plus élevés et des vegas
plus faibles que les options de juillet. Les options de juillet ont une exposition vega plus élevée,
ce qui rend les erreurs de volatilité plus coûteuses en valeur absolue.

Exemples visibles :

| Contrat | Strike | Prix | Théorique | Delta | Gamma | Theta | Vega | IV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| May call | 50 | 1.07 | 0.92 | 44 | 13.4 | -0.0099 | 0.076 | 16.96 |
| May put | 50 | 1.59 | 1.42 | -55 | 13.4 | -0.0098 | 0.076 | 17.30 |
| July call | 50 | 1.88 | 1.67 | 52 | 9.3 | -0.0069 | 0.108 | 16.92 |
| July put | 50 | 1.78 | 1.57 | -46 | 9.3 | -0.0068 | 0.108 | 16.98 |

### Limite

La page seule ne suffit pas à valider tous les chiffres de la table ; les valeurs ci-dessus sont les
points lisibles les plus utiles pour les spreads des pages suivantes.

## Trois spreads candidats — page 175, figure 9-2

La figure compare trois structures sur les options de mai. L'objectif est de montrer que l'edge
théorique ne suffit pas : il faut ensuite comparer les risques portés par chaque construction.

### Spreads initiaux

| Spread | Jambes | Delta position | Edge théorique |
|---|---|---:|---:|
| 1 | Short `10` May 50 calls ; short `8` May 50 puts | 0 | +2.86 |
| 2 | Long `10` May 51 calls ; short `15` May 52 calls | -5 | +1.00 |
| 3 | Long `10` May 49 puts ; short `20` May 50 puts ; long `10` May 51 puts | 0 | +0.40 |

### Enseignement

L'auteur augmente ensuite la taille des spreads 2 et 3 pour obtenir un edge théorique comparable au
spread 1 :

- spread 2 porté à `30 × 45` ;
- spread 3 porté à `70 × 140 × 70`.

Cette mise à taille équivalente force la comparaison sur le risque plutôt que sur le seul edge
initial.

## Spreads ajustés par edge — page 176, figure 9-3

Après ajustement de taille, les trois spreads ont un edge théorique proche, mais des sensibilités
très différentes.

| Spread | Jambes ajustées | Edge | Delta | Gamma | Theta | Vega |
|---|---|---:|---:|---:|---:|---:|
| 1 | Short `10` May 50 calls ; short `8` May 50 puts | +2.86 | 0 | -241.2 | +0.1774 | -1.368 |
| 2 | Long `30` May 51 calls ; short `45` May 52 calls | +3.00 | -15 | -78.0 | +0.0585 | -0.435 |
| 3 | Long `70` May 49 puts ; short `140` May 50 puts ; long `70` May 51 puts | +2.80 | 0 | -98.0 | +0.0770 | -0.630 |

### Enseignement

- Les trois structures sont toutes vega négatif.
- Le short straddle concentre le risque gamma et vega le plus élevé.
- Le ratio vertical spread réduit fortement les sensibilités par rapport au short straddle, mais
  garde un delta résiduel.
- Le long butterfly conserve un delta nul dans cet exemple, avec un gamma/vega intermédiaires.

### Impact projet

Le moteur devra comparer les stratégies après normalisation de l'edge ou du budget de risque. Un
classement brut par edge théorique favorise mécaniquement les tailles plus grandes ou les structures
plus risquées.

## Risque de volatilité — page 178, figures 9-4 et 9-5

Les figures simulent le P&L théorique des trois spreads lorsque la volatilité change.

### Figure 9-4

Hypothèse visuelle : volatilité de départ autour de `15 %`, axe horizontal de `15 %` à `25 %`.

- Les trois spreads commencent avec un edge positif proche.
- Si la volatilité monte, tous les spreads sont pénalisés car ils sont vega négatif.
- Le spread 1, short straddle, perd son edge beaucoup plus vite.
- Le spread 3, long butterfly, garde le profil le plus stable visuellement.

### Figure 9-5

L'axe horizontal visible va environ de `10 %` à `24 %`.

- À volatilité plus basse, les structures vega négatif peuvent gagner davantage que l'edge initial.
- À volatilité plus haute, le short straddle reste le plus sensible.
- Les comparaisons doivent donc utiliser une plage de volatilité, pas un seul point de modèle.

### Impact projet

Pour chaque structure candidate, le futur outil devra produire un stress test de volatilité :

- scénario IV modèle ;
- scénarios IV plus bas et plus haut ;
- point où l'edge disparaît ;
- pente de perte autour de l'IV actuelle ;
- comparaison entre structures à edge comparable.

## Rho et gamma risk — page avec figure 9-6

### Rho

Le passage indique que le risque de taux existe, mais qu'il est généralement moins important que les
autres entrées du modèle pour l'évaluation d'options, sauf cas spéciaux.

Cette observation ne supprime pas le besoin de rho : elle le place derrière volatilité, gamma,
theta, liquidité et structure de maturité dans la plupart des comparaisons.

### Gamma risk — figure 9-6

La figure compare les trois spreads selon le prix du sous-jacent, avec hypothèse de valeur théorique
approximativement comparable au prix courant du sous-jacent `49.50`.

Lecture visuelle :

- Tous les spreads ont un gamma négatif.
- Le short straddle a la courbure la plus défavorable lorsque le sous-jacent s'éloigne du centre.
- Le ratio vertical spread déplace le risque vers un côté selon les strikes.
- Le long butterfly concentre son avantage près de la zone centrale et perd lorsque le sous-jacent
  sort de cette zone.

### Impact projet

Le stress test ne doit pas être seulement un stress d'IV. Il faut aussi une grille de sous-jacent :

- prix actuel ;
- baisses et hausses autour du prix actuel ;
- zones de break-even théorique ;
- courbure/gamma ;
- perte en cas de gap ;
- interaction entre changement de prix et changement d'IV.

## Conclusions provisoires pour Take Two

1. L'edge théorique doit être comparé après sizing équivalent ou budget de risque équivalent.
2. Deux stratégies au même edge peuvent porter des risques gamma, theta et vega très différents.
3. Les structures short volatility doivent être stressées contre des hausses d'IV.
4. Les structures short gamma doivent être stressées contre des mouvements du sous-jacent.
5. Le choix ne peut pas se faire sur le nom de la stratégie : il dépend des jambes, quantités,
   strikes, maturités et hypothèses.
6. Le rho est documenté mais ne doit pas prendre le dessus sur les risques dominants sauf contexte
   spécial.
7. Cette revue confirme que le futur script IBKR doit d'abord être un moteur de comparaison et de
   stress, pas un moteur d'ordre automatique.

## Prochaine page attendue

Pages imprimées autour de 179–181 :

- texte complet autour de la figure 9-6 ;
- discussion de `theta risk` et coûts de portage ;
- passage sur l'exécution/liquidité qui mène à la règle `R-OPTIONS-001`.
