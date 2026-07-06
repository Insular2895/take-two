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

## Deuxième groupe de spreads — pages 183–185, figures 9-7 à 9-10

### Figure 9-7 — spreads 4, 5 et 6

La figure compare trois autres structures, avec leurs edges et sensibilités agrégées :

| Spread | Jambes | Edge | Delta | Gamma | Theta | Vega |
|---|---|---:|---:|---:|---:|---:|
| 4 | Long `20` July 50 calls ; short `30` July 52 calls | +2.70 | +20 | -72.0 | +0.0570 | -0.840 |
| 5 | Long `50` May 48 puts ; short `50` July 48 puts | +3.00 | -50 | +180.0 | -0.1350 | -1.850 |
| 6 | Long `10` May 48 calls ; short `20` July 52 calls | +2.90 | +20 | -56.0 | +0.0470 | -1.340 |

### Figures 9-8 à 9-10

Les figures comparent ces trois spreads selon :

- la volatilité ;
- le prix du sous-jacent ;
- le temps restant jusqu'à expiration.

Lecture documentaire :

- si le risque principal est une hausse d'IV, le spread 4 paraît le plus défensif ;
- si le risque principal est un grand mouvement du sous-jacent, le spread 5 est favorisé par son
  gamma positif ;
- si l'on accepte une protection partielle contre plusieurs risques, le spread 6 devient un
  compromis.

Le texte insiste sur le fait que le choix n'est pas une question de vrai/faux, mais de risque que le
trader accepte de porter.

## Méthode rapide `risque / edge` — pages 186–187

Natenberg propose une approximation pratique pour comparer rapidement plusieurs spreads :

```text
ratio_de_risque = sensibilité pertinente / theoretical edge
```

La sensibilité placée au numérateur dépend du risque principal :

- risque de volatilité : `vega / theoretical edge` ;
- risque de grand mouvement du sous-jacent : `gamma / theoretical edge` ;
- autres sensibilités possibles selon le contexte.

### Exemple vega, spreads 4 à 6

| Spread | Calcul | Ratio |
|---|---:|---:|
| 4 | -0.840 / 2.70 | -0.311 |
| 5 | -1.850 / 3.00 | -0.617 |
| 6 | -1.340 / 2.90 | -0.462 |

Le spread 4 a le ratio vega/edge le plus proche de zéro : il porte donc, dans cette approximation,
le meilleur compromis vis-à-vis de la volatilité.

### Exemple gamma, spreads 4 et 6

| Spread | Calcul | Ratio |
|---|---:|---:|
| 4 | -72.0 / 2.70 | -26.7 |
| 6 | -56.0 / 2.90 | -19.3 |

Le spread 6 est moins exposé au risque de grand mouvement que le spread 4 selon ce ratio.

### Avertissement

L'auteur avertit que les sensibilités ne sont bien définies que dans une plage étroite. Ce ratio
donne une approximation de risque relatif, pas une vérité globale. Il peut alerter contre une
structure manifestement fragile, mais ne remplace pas les stress graphs.

### Exemple vega, spreads 1 à 3

| Spread | Calcul | Ratio |
|---|---:|---:|
| 1 | -1.368 / 2.86 | -0.478 |
| 2 | -0.435 / 3.00 | -0.145 |
| 3 | -0.630 / 2.80 | -0.225 |

Le ratio ferait préférer le spread 2 pour le risque de volatilité, mais la figure 9-4 montre que le
spread 3 a le profil de volatilité le moins défavorable. Le ratio est donc un filtre rapide, pas un
classement final.

## Marge d'erreur et sizing — pages 187–188

La section `How Much Margin for Error?` reformule le problème : il ne faut pas seulement demander
quelle marge d'erreur est raisonnable, mais quelle taille de position est acceptable pour une marge
d'erreur donnée.

Enseignements :

- une stratégie avec faible marge d'erreur doit rester petite ;
- une stratégie avec marge d'erreur large peut supporter une taille plus grande ;
- la taille dépend de ce qui peut mal tourner avant que la stratégie se retourne contre le trader ;
- straddles et strangles sont signalés comme les spreads les plus risqués, qu'ils soient achetés ou
  vendus, car ils offrent peu de marge d'erreur.

### Impact projet

Le futur outil devra séparer :

- edge théorique ;
- marge d'erreur par risque dominant ;
- taille proposée ;
- perte si l'hypothèse est fausse ;
- capacité réelle d'exécution.

Un score ne doit pas grossir automatiquement une position parce que l'edge est positif.

## Dividendes et taux — pages 188–192, figures 9-11 à 9-14

### Figure 9-11 — table stock options

Hypothèses visibles :

- stock price `98 1/2` ;
- volatilité modèle : mars `27 %`, juin `27 %` ;
- taux : `8 %` ;
- dividende attendu : `1.25` ;
- maturités : mars `56 jours`, juin `147 jours`.

La table fournit prix, valeur théorique, delta, gamma, theta, vega et IV pour calls/puts de mars et
juin.

### Figure 9-12 — quatre spreads

| Spread | Jambes | Edge | Delta | Gamma | Theta | Vega |
|---|---|---:|---:|---:|---:|---:|
| 7 | Long `25` June 95 puts ; short `25` March 95 puts | +6.75 | -75 | -32.5 | +0.3400 | +2.275 |
| 8 | Long `15` June 100 calls ; short `15` March 100 calls | +6.45 | +75 | -21.0 | +0.2070 | +1.380 |
| 9 | Long `15` June 95 puts ; short `10` March 100 puts | +6.50 | -35 | -3.5 | +0.0495 | +1.985 |
| 10 | Long `18` June 105 calls ; short `10` March 95 calls | +6.14 | +44 | +5.40 | -0.0464 | +2.774 |

### Figure 9-13 — intérêt

La figure montre que :

- spreads 7 et 9 sont pénalisés par une hausse des taux ;
- spreads 8 et 10 sont aidés par une hausse des taux.

Si la hausse des taux est le risque prioritaire, les spreads 8 et 10 deviennent les meilleurs
candidats, indépendamment de certaines qualités vega/gamma des spreads 7 et 9.

Comparaison rapide du vega :

| Spread | Calcul | Ratio |
|---|---:|---:|
| 8 | 1.380 / 6.45 | 0.214 |
| 10 | 2.774 / 6.14 | 0.452 |

Si le risque de volatilité est la deuxième préoccupation, le spread 8 est préféré au spread 10. Si
le risque de grand mouvement du sous-jacent domine, le spread 10 peut être préféré car son gamma est
positif.

### Figure 9-14 — dividendes

La figure montre que si le dividende augmente :

- spreads 7 et 9 sont aidés ;
- spreads 8 et 10 sont pénalisés.

Comparaison rapide des spreads 7 et 9 :

| Spread | Vega risk | Gamma risk |
|---|---:|---:|
| 7 | 2.275 / 6.75 = 0.337 | -32.5 / 6.75 ≈ -4.8 |
| 9 | 1.985 / 6.50 = 0.305 | -3.5 / 6.50 ≈ -0.5 |

Le texte indique que si l'écart de vega est faible, le spread 9 peut être préféré car il porte
beaucoup moins de gamma risk. Si la hausse de dividende est très probable, le spread 7 peut rester
préférable car il bénéficie davantage de cette hausse.

### Impact projet

La comparaison de spreads sur actions doit intégrer :

- taux ;
- dividendes attendus ;
- sensibilité des maturités aux taux/dividendes ;
- arbitrage entre risque prioritaire et risques secondaires.

## Bon spread, marge d'erreur et survie — pages 192–193

Le texte définit un bon spread non pas comme celui qui gagne le plus quand tout va bien, mais comme
celui qui perd le moins quand tout va mal.

Conséquences pour Take Two :

- le score doit valoriser la survie et la perte contrôlée ;
- un trade perdant peut être un bon choix s'il évite une perte beaucoup plus grande ;
- les winning trades se gèrent plus facilement que les losing trades ; la priorité est donc de
  limiter les pertes qui effacent les gains.

## Ajustements — pages 193–195

Le chapitre distingue deux familles d'ajustements :

- ajustement avec le sous-jacent : change le delta sans changer gamma, theta et vega ;
- ajustement avec options : change le delta mais modifie aussi gamma, theta et vega.

### Exemple short strangle

Position initiale :

```text
short 20 strangles 95/105
delta initial = (-20 × -36) + (-20 × +36) = 0
```

Après baisse du sous-jacent à `97.00` :

```text
delta = (-20 × -41) + (-20 × +30) = +220
```

Trois choix sont évoqués :

1. vendre le sous-jacent ;
2. vendre des calls ;
3. acheter des puts.

L'ajustement par achat de puts réduit plusieurs risques mais réduit aussi l'edge théorique si les
puts restent chers. L'ajustement par vente de calls augmente l'edge mais grossit la position.

Après rebond à `101.50`, l'exemple montre que l'ajustement répété par vente d'options peut faire
passer la position de `20` strangles à `42 × 27`, ce qui magnifie le risque en cas de mouvement
violent.

### Règle documentaire

Une amélioration d'edge ne suffit jamais à justifier un ajustement si elle augmente trop la taille
ou le risque total. À partir d'un certain point, il faut réduire la taille ou ajuster dans le
sous-jacent.

## Style de trading et gamma — pages 195–196

La section `A Question of Style` lie le signe du gamma au style de hedge :

- gamma négatif : les ajustements suivent la tendance du sous-jacent ;
- gamma positif : les ajustements vont contre la tendance du sous-jacent.

Le texte précise qu'un trader qui préfère suivre la tendance ou trader contre la tendance doit
choisir une combinaison stratégie + fréquence d'ajustement compatible avec son style. Pour un moteur
automatisé, cela signifie que le style de couverture doit être un paramètre explicite, pas une
hypothèse cachée.

## Liquidité — pages 196–198, figure 9-15

### Principes

Un marché liquide rend l'entrée, la sortie et l'ajustement plus faciles. Un marché illiquide peut
forcer le trader à garder la position jusqu'à expiration ou à sortir à un prix défavorable.

Points contrôlés :

- les options court terme proches de la monnaie sont généralement plus liquides ;
- les options long terme ou profondément ITM/OTM ont souvent des spreads bid/ask plus larges ;
- il faut aussi vérifier la liquidité du sous-jacent, surtout si les ajustements se font avec lui ;
- le cas le plus dangereux combine options illiquides et sous-jacent illiquide.

### Figure 9-15

La figure donne des bid/ask/volume S&P 500 index options par maturité. Elle illustre :

- volumes très différents selon échéance et strike ;
- `no listing` sur certaines options ;
- bid/ask beaucoup plus larges sur certaines maturités ou moneyness ;
- nécessité de regarder chaque jambe, pas seulement la structure agrégée.

### Impact projet

Avant tout signal exécutable, le futur module IBKR devra appliquer un filtre de liquidité par jambe :

- bid disponible ;
- ask disponible ;
- spread bid/ask acceptable ;
- volume et open interest suffisants ;
- taille disponible pour la quantité cible ;
- possibilité de sortir ou d'ajuster ;
- liquidité du sous-jacent si hedge prévu.

## Conclusions provisoires pour Take Two

1. L'edge théorique doit être comparé après sizing équivalent ou budget de risque équivalent.
2. Deux stratégies au même edge peuvent porter des risques gamma, theta et vega très différents.
3. Les structures short volatility doivent être stressées contre des hausses d'IV.
4. Les structures short gamma doivent être stressées contre des mouvements du sous-jacent.
5. Le choix ne peut pas se faire sur le nom de la stratégie : il dépend des jambes, quantités,
   strikes, maturités et hypothèses.
6. Le rho est documenté mais ne doit pas prendre le dessus sur les risques dominants sauf contexte
   spécial.
7. Le ratio `sensibilité / edge` peut servir de filtre rapide, mais ne remplace pas les stress
   tests.
8. La taille doit dépendre de la marge d'erreur, pas seulement de l'edge.
9. Un ajustement par options peut améliorer l'edge tout en grossissant dangereusement le risque.
10. La liquidité de chaque jambe et du sous-jacent est une condition préalable.
11. Cette revue confirme que le futur script IBKR doit d'abord être un moteur de comparaison et de
   stress, pas un moteur d'ordre automatique.

## Prochaine page attendue

Pages imprimées après 198, si le chapitre continue :

- suite ou conclusion après la figure 9-15 ;
- tout passage final qui résume les critères d'entrée/sortie ou d'exécution.
