# Revue visuelle — B-NATENBERG-1994 — Chapitre 8

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Chapitre : 8 — Volatility Spreads.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
valeurs utiles et limites contrôlées visuellement.

## Backspreads — pages 138–139, figures 8-1 et 8-2

### Construction

- Call backspread : davantage de calls longs au strike haut que de calls courts au strike bas,
  même échéance.
- Put backspread : davantage de puts longs au strike bas que de puts courts au strike haut, même
  échéance.
- La structure vise initialement un delta proche de zéro, mais les exemples ne sont pas
  nécessairement parfaitement neutres.
- Le montage est généralement initié pour un crédit dans les exemples du livre.

### Profil

- Un grand mouvement vers le côté des options longues produit un potentiel non borné.
- Le côté opposé présente un potentiel limité.
- L'absence de mouvement peut conduire à une perte.
- Le call backspread favorise surtout une forte hausse ; le put backspread une forte baisse.

### Exemples affichés

- Calls mars : long `30` calls `105`, short `10` calls `95`.
- Calls juin : long `25` calls `110`, short `10` calls `100`.
- Puts mars : long `80` puts `90`, short `10` puts `100`.
- Puts juin : long `45` puts `95`, short `30` puts `100`.

### Limite

Le graphique est un payoff à expiration. Il ne montre pas le chemin du P&L avant expiration, les
variations d'IV ni le coût d'exécution.

## Ratio vertical spreads — pages 139–140, figures 8-3 et 8-4

### Construction

- Structure opposée au backspread : davantage d'options courtes que longues, même échéance.
- Call ratio vertical : calls longs au strike bas et davantage de calls courts au strike haut.
- Put ratio vertical : puts longs au strike haut et davantage de puts courts au strike bas.

### Profil

- Profit maximal autour du strike des options courtes.
- Call ratio vertical : risque important lors d'une forte hausse.
- Put ratio vertical : risque important lors d'une forte baisse.
- Le livre associe ce montage à une attente de marché relativement stable, avec biais directionnel
  selon le côté choisi.

### Impact projet

Le moteur ne doit pas présenter un ratio spread sans scénario de queue, perte maximale simulée et
contrôle de marge.

## Straddles — pages 141–142, figures 8-5 et 8-6

### Construction

- Long straddle : call long et put long de même strike et même échéance.
- Short straddle : call court et put court de même strike et même échéance.

### Profil

- Long straddle : perte limitée à la prime, potentiel important dans les deux directions, besoin
  d'un mouvement suffisamment grand.
- Short straddle : profit limité à la prime, maximum près du strike, fortes pertes lorsque le marché
  s'éloigne fortement.
- Le texte avertit qu'une probabilité élevée de petit profit ne suffit pas si les pertes rares sont
  disproportionnées.

### Limite

Le payoff à expiration ne mesure pas le risque de variation d'IV, de gap ou de marge avant
expiration.

## Strangles — pages 143–144, figures 8-7 et 8-8

### Construction

- Call et put de même échéance mais de strikes différents.
- Long strangle : achat des deux options.
- Short strangle : vente des deux options.

### Profil

- Le long strangle coûte généralement moins cher qu'un straddle, mais nécessite un mouvement plus
  important pour devenir profitable.
- Le livre le décrit comme davantage levierisé en pourcentage.
- Le short strangle recherche un marché stable, avec risque de queue des deux côtés.
- Le ratio call/put n'est pas nécessairement `1:1`.

## Butterflies — page 146, figures 8-9 et 8-10

### Construction

- Long butterfly : achat des ailes basse et haute, vente de deux options au strike central.
- Short butterfly : vente des ailes, achat de deux options au strike central.
- Toutes les options sont du même type et de même échéance.

### Profil

- Long butterfly : profit maximal près du strike central ; gains et pertes bornés.
- Short butterfly : perte maximale près du strike central ; bénéficie d'un éloignement important.

### Limite visuelle

Une bande rouge masque une partie de la figure 8-10. La structure et la forme générale restent
lisibles, mais aucune valeur verticale précise n'est transcrite.

## Time spreads — pages 149–152, figures 8-11 à 8-14

### Construction

- Long time spread : option longue échéance achetée et option courte échéance vendue au même
  strike.
- Short time spread : opération inverse.
- Les figures 8-11 et 8-12 montrent la valeur au moment de l'expiration proche, pas le payoff final
  des deux options.

### Effet du passage du temps — figure 8-13

| Temps long terme | Temps court terme | Valeur option longue | Valeur option courte | Valeur spread |
|---:|---:|---:|---:|---:|
| 6 mois | 3 mois | 7 1/2 | 6 | 1 1/2 |
| 5 mois | 2 mois | 7 1/4 | 5 | 2 1/4 |
| 4 mois | 1 mois | 6 3/4 | 3 | 3 3/4 |
| 3 mois | 0 | 6 | 0 | 6 |

Dans cet exemple à conditions inchangées, le long time spread s'élargit lorsque l'échéance courte
approche.

### Effet de la volatilité — figure 8-14

| Volatilité | Option longue | Option courte | Valeur spread |
|---:|---:|---:|---:|
| 15 % | 6 1/2 | 5 1/2 | 1 |
| 20 % | 7 1/2 | 6 | 1 1/2 |
| 25 % | 8 1/2 | 6 1/2 | 2 |

Dans cet exemple, une hausse d'IV élargit le long time spread car l'option longue réagit davantage.

### Limite

Ces tableaux supposent notamment une relation stable entre les autres variables. Ils ne constituent
pas une règle générale de profit.

## Taux et dividendes — page 156, figure 8-15

Hypothèses : sous-jacent `100`, volatilité `20 %`, échéance mars `6 semaines`, échéance juin
`19 semaines`.

### Effet des taux

| Taux | Call spread | Put spread |
|---:|---:|---:|
| 0 % | 2.10 | 2.10 |
| 3 % | 2.47 | 1.73 |
| 6 % | 2.87 | 1.39 |
| 9 % | 3.28 | 1.09 |
| 12 % | 3.72 | 0.82 |

Une hausse des taux élargit le call time spread et réduit le put time spread dans cet exemple.

### Effet des dividendes

Taux fixé à `6 %`.

| Dividende trimestriel | Call spread | Put spread |
|---:|---:|---:|
| 0 | 2.87 | 1.39 |
| 1 | 2.28 | 1.78 |
| 2 | 1.75 | 2.25 |
| 3 | 1.31 | 2.79 |
| 4 | 0.95 | 3.39 |

Une hausse du dividende réduit le call spread et élargit le put spread dans cet exemple.

### Impact projet

Taux, dividendes et corporate actions sont obligatoires pour valoriser et comparer des calendars.

## Variantes — pages 158–159, figures 8-16 à 8-18

- Christmas tree : variante asymétrique combinant plusieurs strikes.
- Iron butterfly : combinaison call-put équivalente économiquement à un butterfly sous les
  hypothèses de parité.
- Condor : butterfly dont les deux options centrales utilisent des strikes différents, donnant une
  zone de profit maximal plus large.
- Le chapitre fournit des exemples longs et courts pour calls et puts.

Ces structures augmentent le nombre de jambes et renforcent le besoin de contrôler liquidité,
bid-ask cumulé, marge et risque de legging.

## Carte des sensibilités — page 161, figure 8-19

| Spread | Delta initial | Gamma | Theta | Vega |
|---|---|---|---|---|
| Backspread | 0 | + | - | + |
| Long straddle | 0 | + | - | + |
| Long strangle | 0 | + | - | + |
| Short butterfly | 0 | + | - | + |
| Ratio vertical spread | 0 | - | + | - |
| Short straddle | 0 | - | + | - |
| Short strangle | 0 | - | + | - |
| Long butterfly | 0 | - | + | - |
| Long time spread | 0 | - | + | + |
| Short time spread | 0 | + | - | - |

### Interprétation

- Gamma positif et theta négatif vont ensemble dans ce cadre.
- Gamma négatif et theta positif vont ensemble.
- Le vega ne suit pas toujours le gamma : le long time spread est gamma négatif mais vega positif.
- Le delta zéro est un état initial approximatif ; il change avec le marché.

## Exemples numériques — pages 162–164, figure 8-20

### Agrégats contrôlés

| Structure | Échéance/exemple | Delta | Gamma | Theta | Vega |
|---|---|---:|---:|---:|---:|
| Call backspread | Mars | -60 | +95.0 | -0.5290 | +2.210 |
| Call backspread | Juin | +65 | +30.5 | -0.1640 | +2.210 |
| Put backspread | Mars | -20 | +78.0 | -0.4070 | +1.860 |
| Put backspread | Juin | +15 | +34.5 | -0.1815 | +2.385 |
| Call ratio vertical | Mars | +30 | -88.0 | +0.4970 | -2.020 |
| Call ratio vertical | Juin | +90 | -39.0 | +0.2300 | -2.880 |
| Put ratio vertical | Mars | -60 | -16.0 | +0.0760 | -0.400 |
| Put ratio vertical | Juin | 0 | -19.0 | +0.1085 | -1.365 |
| Long straddle | Mars | +30 | +116.0 | -0.6260 | +2.680 |
| Short straddle | Juin | -80 | -128.0 | +0.6640 | -9.360 |
| Long strangle | Mars | +60 | +178.0 | -0.9640 | +4.140 |
| Short strangle | Juin | -50 | -59.0 | +0.2890 | -4.300 |

### Enseignements

- Deux implémentations du même type de spread peuvent avoir des deltas très différents.
- Le nom de la stratégie ne suffit pas à décrire son risque.
- Quantités, strikes, maturités et valeurs de marché doivent être agrégés avant classification.

## Butterflies et time spreads numériques — pages 165–166

### Agrégats contrôlés

| Structure | Exemple | Delta | Gamma | Theta | Vega |
|---|---|---:|---:|---:|---:|
| Long butterfly | Calls mars | 0 | -27.0 | +0.1550 | -0.610 |
| Long butterfly | Puts juin | -60 | -15.0 | +0.0750 | -0.900 |
| Short butterfly | Puts mars | -220 | +22.0 | -0.1280 | +0.500 |
| Short butterfly | Calls juin | -25 | +12.5 | -0.0800 | +0.950 |
| Long time spread | Calls strike 100 | 0 | -52.0 | +0.2940 | +2.000 |
| Long time spread | Puts strike 95 | -100 | -14.0 | +0.0810 | +1.090 |
| Short time spread | Puts strike 100 | environ -25 | +65.0 | -0.3675 | -2.500 |
| Diagonal agissant comme short time spread | Calls 105/110 | +10 | +21.0 | -0.1180 | -0.750 |

### Enseignements

- Le ratio `1 × 2 × 1` d'un butterfly ne garantit pas un delta nul lorsque les strikes sont loin du
  sous-jacent.
- Le long butterfly est ici gamma négatif, theta positif et vega négatif.
- Le short butterfly inverse ces expositions, mais peut conserver un delta directionnel important.
- Le long time spread combine gamma négatif, theta positif et vega positif.
- Le short time spread combine gamma positif, theta négatif et vega négatif.
- Un diagonal peut se comporter comme un time spread lorsque les deltas des jambes sont proches.

### Règle de sélection présentée par l'auteur

- Si l'IV de marché est globalement inférieure à l'estimation de volatilité, examiner les structures
  à vega positif, notamment backspreads et longs time spreads.
- Si l'IV est globalement supérieure à l'estimation, examiner les structures à vega négatif,
  notamment ratio verticals et shorts time spreads.

Cette règle n'est qu'un filtre de candidats. Le texte annonce immédiatement que les straddles et
strangles peuvent avoir un edge théorique élevé tout en faisant partie des structures les plus
risquées. Le chapitre 9 doit donc être appliqué avant toute conclusion.

## IV et structure par terme — page 167, figures 8-21 et 8-22

- Sous-jacent futures : `100`.
- Échéance mars : `6 semaines`.
- Échéance juin : `13 semaines`.
- Volatilité du modèle : `20 %`.
- Taux : `6 %`.
- Deux niveaux de volatilité implicite de marché : `17 %` et `23 %`.

Les valeurs théoriques basées sur le modèle restent identiques entre les deux tableaux, tandis que
les prix de marché changent avec l'IV. La valeur relative d'un time spread dépend donc de l'IV de
chaque maturité, pas d'une IV unique appliquée aveuglément.

## Tickets de spread historiques — pages 171–172, figures 8-23a et 8-23b

Les figures montrent notamment :

- sens achat/vente de chaque jambe ;
- ratio du spread ;
- prix net en débit ou crédit ;
- instruction `All or None` ;
- identification du spread plutôt que deux ordres indépendants.

### Limite

Ces tickets sont historiques. Ils servent uniquement à dériver les champs conceptuels d'un ordre
multi-jambes. Les règles opérationnelles devront venir de la documentation IBKR actuelle.

## Conclusions pour Take Two

1. Une stratégie doit être représentée par ses jambes réelles, pas seulement par un nom.
2. Payoff à expiration, P&L avant expiration et Greeks sont trois vues distinctes.
3. Le delta initialement neutre ne garantit aucune neutralité future.
4. Les structures short gamma exigent une analyse explicite des queues et de la marge.
5. Les time spreads nécessitent une surface d'IV par maturité, ainsi que taux et dividendes.
6. Le score doit être calculé après bid-ask, commissions, liquidité et risque de legging.
7. Les anciens tickets ne constituent aucune instruction d'exécution actuelle.

## Suite documentaire

La revue du chapitre 9 est maintenant séparée dans :

- `visual_reviews/B-NATENBERG-1994-CH09.md`.

Le chapitre 8 sert de carte des structures ; le chapitre 9 sert à comparer leur edge théorique aux
risques gamma, theta, vega, taille et exécution.
