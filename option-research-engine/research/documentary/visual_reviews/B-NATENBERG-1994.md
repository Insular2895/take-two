# Revue visuelle — B-NATENBERG-1994

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Statut : `in_progress`

Méthode : contrôle page par page à partir d'images fournies par l'utilisateur. Les images du livre
ne sont pas versionnées. Seuls les identifiants de figures, hypothèses visibles, observations et
limites sont conservés.

Suite dédiée au chapitre 8 :
`B-NATENBERG-1994-CH08.md`.

## Page imprimée 104 — Figures 6-6 et 6-7

Date de revue : 2026-07-05.

### Contenu vérifié

- Figure 6-6 : `Call Delta vs. Underlying Price`.
- Figure 6-7 : `Put Delta vs. Underlying Price`.
- Temps restant : `60 jours`.
- Volatilité : `20 %`.
- Strikes représentés : `90`, `100`, `110`.
- Sous-jacent représenté approximativement de `80` à `120`.

### Observation documentaire

- Le delta d'un call progresse vers `100` lorsque le sous-jacent dépasse fortement le strike.
- Le delta d'un put progresse vers `0` lorsque le sous-jacent dépasse fortement le strike et vers
  `-100` dans le sens opposé.
- La transition la plus rapide se produit autour du strike.
- La courbe se déplace avec le strike : la sensibilité dépend donc de la moneyness, pas seulement du
  niveau absolu du sous-jacent.

### Limite

Le graphique permet une lecture qualitative et des valeurs approximatives. Il ne constitue pas une
table numérique suffisamment précise pour calibrer un modèle.

### Impact projet

Confirme visuellement `R-GREEKS-002` : une position initialement delta-neutre cesse de l'être lorsque
le sous-jacent change.

## Page imprimée 107 — Figures 6-8 et 6-9

Date de revue : 2026-07-05.

### Contenu vérifié

- Figure 6-8 : `Call or Put Gamma vs. Underlying Price`.
- Hypothèses : `60 jours`, volatilité `20 %`.
- Strikes représentés : `90`, `100`, `110`.
- Figure 6-9 : `Call or Put Gamma vs. Time to Expiration`.
- Hypothèses : sous-jacent `100`, volatilité `20 %`.
- Échéances représentées approximativement de `0` à `200 jours`.

### Observation documentaire

- Pour chaque strike, le gamma atteint son maximum lorsque le sous-jacent est proche du strike.
- À prix du sous-jacent donné, le gamma de l'option ATM augmente fortement à l'approche de
  l'expiration.
- Pour les options éloignées du strike, le gamma tend au contraire vers zéro à l'approche de
  l'expiration.
- Les options non-ATM présentent un maximum de gamma à une maturité intermédiaire dans le graphique.
- Le risque de variation rapide du delta est donc concentré différemment selon la moneyness et le
  temps restant.

### Valeurs uniquement indicatives

- Figure 6-8 : pics de gamma visuellement proches de `5.5`, `5.0` et `4.5` pour les strikes `90`,
  `100` et `110`.
- Figure 6-9 : le gamma ATM dépasse l'échelle de `25` au voisinage immédiat de l'expiration.

Ces lectures ne doivent pas être utilisées comme seuils ou données de calibration.

### Impact projet

- Renforce `R-GREEKS-002` : la fréquence de recalcul du delta dépend du gamma.
- Renforce `R-GREEKS-003` : un long gamma proche du strike et de l'expiration doit être évalué avec
  son theta et ses coûts de couverture.
- Exigence future : le moteur IBKR devra calculer gamma par strike et maturité, puis agréger le
  gamma de la position complète.

## Page imprimée 108 — Figures 6-10 et 6-11

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-10 : `Call or Put Gamma vs. Volatility`.
- Hypothèses : sous-jacent `100`, temps restant `60 jours`.
- Strikes représentés : `90`, `100`, `110`.
- Volatilité représentée approximativement de `0 %` à `40 %`.
- Figure 6-11 : `Call Delta vs. Time to Expiration`.
- Hypothèses : sous-jacent `100`, volatilité `20 %`.
- Échéances représentées approximativement de `0` à `200 jours`.

### Observation documentaire — gamma et volatilité

- Pour le strike ATM `100`, le gamma est extrêmement élevé lorsque la volatilité est faible, puis
  diminue fortement lorsque la volatilité augmente.
- Pour les strikes non-ATM `90` et `110`, le gamma est proche de zéro lorsque la volatilité est très
  faible.
- Le gamma non-ATM augmente ensuite avec la volatilité, atteint un maximum intermédiaire, puis
  diminue légèrement.
- Une même hausse de volatilité peut donc réduire le gamma ATM tout en augmentant initialement le
  gamma d'une option éloignée du strike.

### Observation documentaire — delta et temps

- Le call ITM de strike `90` a un delta proche de `100` à très courte échéance ; son delta diminue
  lorsque la maturité s'allonge.
- Le call ATM de strike `100` reste proche d'un delta de `50`, avec une légère augmentation sur le
  graphique.
- Le call OTM de strike `110` a un delta proche de zéro à très courte échéance ; son delta augmente
  lorsque davantage de temps reste avant expiration.
- L'allongement de la maturité rapproche donc les deltas extrêmes de valeurs intermédiaires dans
  cet exemple.

### Valeurs uniquement indicatives

- Figure 6-10 : gamma ATM visuellement supérieur à `20` autour de `5 %` de volatilité et proche de
  `2.5` vers `40 %`.
- Figure 6-11 : à `200 jours`, deltas visuellement proches de `78`, `53` et `29` pour les strikes
  `90`, `100` et `110`.

Ces lectures servent à contrôler le sens et la forme des relations, pas à calibrer des seuils.

### Impact projet

- Le moteur devra recalculer gamma après changement d'IV, même si le sous-jacent ne bouge pas.
- La priorité de surveillance d'un gamma ne peut pas être déduite de la seule proximité du strike :
  maturité et volatilité sont également nécessaires.
- Le calcul du delta devra intégrer simultanément moneyness, temps restant et volatilité.
- `R-GREEKS-002` et `R-GREEKS-003` sont confirmées qualitativement, sans validation quantitative.

## Pages imprimées 109–110 — Figures 6-12 à 6-14

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-12 : `Put Delta vs. Time to Expiration`.
- Hypothèses : sous-jacent `100`, volatilité `20 %`.
- Figure 6-13 : `Call Delta vs. Volatility`.
- Figure 6-14 : `Put Delta vs. Volatility`.
- Hypothèses des figures 6-13 et 6-14 : sous-jacent `100`, temps restant `60 jours`.
- Strikes représentés : `90`, `100`, `110`.

### Observation documentaire

- À très courte échéance, les deltas des options ITM tendent vers `100` pour les calls et `-100`
  pour les puts ; les deltas OTM tendent vers zéro.
- Quand la maturité augmente, les deltas extrêmes se rapprochent de valeurs intermédiaires.
- Une hausse de volatilité produit un effet analogue : le delta d'un call ITM diminue et celui d'un
  call OTM augmente.
- Pour les puts, le delta OTM devient plus négatif lorsque la volatilité augmente, tandis que le
  delta ITM devient moins négatif.
- Les deltas ATM restent proches de `50` pour les calls et de `-50` pour les puts dans ces exemples.

### Valeurs uniquement indicatives

- À `200 jours`, les deltas des puts de strikes `90`, `100` et `110` sont visuellement proches de
  `-22`, `-47` et `-71`.
- À `40 %` de volatilité, les deltas des calls sont visuellement proches de `77`, `53` et `31`.
- À `40 %` de volatilité, les deltas des puts sont visuellement proches de `-23`, `-47` et `-70`.

Une bande rouge masque une partie de la figure 6-13, mais les courbes et leurs tendances restent
lisibles. Ces nombres ne sont pas des valeurs de calibration.

### Impact projet

- Confirme que le delta doit être recalculé après changement de temps ou d'IV, même sans mouvement
  du sous-jacent.
- Interdit d'utiliser un delta statique comme probabilité permanente jusqu'à l'expiration.
- Renforce `R-GREEKS-002` et le conflit ouvert `C-001`.

## Pages imprimées 112–113 — Figures 6-15 à 6-17

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-15 : `Call Theoretical Value vs. Time to Expiration`.
- Figure 6-16 : `Put Theoretical Value vs. Time to Expiration`.
- Figure 6-17 : `Call or Put Theta vs. Time to Expiration`.
- Hypothèses : sous-jacent `100`, volatilité `20 %`.
- Strikes représentés : `90`, `100`, `110`.

### Observation documentaire

- À l'expiration, les options ITM convergent vers leur valeur intrinsèque et les options ATM/OTM
  vers zéro dans les graphiques.
- La valeur théorique augmente avec le temps restant pour les trois niveaux de moneyness.
- Le theta ATM du strike `100` s'accélère très fortement à l'approche de l'expiration.
- Le theta des options éloignées du strike tend vers zéro à très courte échéance et présente un
  maximum à une maturité intermédiaire.
- L'expression « le theta accélère près de l'expiration » n'est donc pas uniformément applicable à
  toutes les options : la moneyness est déterminante.

### Valeurs uniquement indicatives

- Le theta ATM dépasse visuellement `0.20` au voisinage immédiat de l'expiration.
- Les courbes des strikes `90` et `110` restent très inférieures et culminent autour d'une maturité
  intermédiaire.

### Impact projet

- Le moteur devra représenter le theta comme une fonction de la maturité et de la moneyness.
- Une alerte d'expiration fondée sur un nombre fixe de jours serait insuffisante sans theta calculé.
- Renforce `R-GREEKS-003` : le coût theta d'un long gamma varie fortement avec le placement du
  strike et le temps restant.

## Pages imprimées 114–115 — Figures 6-18 et 6-19

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-18 : `Call Theoretical Value vs. Volatility`.
- Figure 6-19 : `Put Theoretical Value vs. Volatility`.
- Hypothèses : sous-jacent `100`, temps restant `60 jours`.
- Strikes représentés : `90`, `100`, `110`.
- Volatilité représentée approximativement de `0 %` à `40 %`.

### Observation documentaire

- La valeur théorique des calls et des puts augmente lorsque la volatilité augmente.
- À volatilité proche de zéro, les options ITM sont proches de leur valeur intrinsèque et les
  options ATM/OTM proches de zéro dans cet exemple.
- L'option ATM montre une augmentation absolue importante.
- Le texte de la page 115 distingue sensibilité absolue et sensibilité relative : une option OTM
  peut avoir la plus forte variation en pourcentage tout en gagnant moins de points qu'une ATM.
- Le texte annonce aussi que le vega diminue à l'approche de l'expiration, point à vérifier sur la
  figure 6-20.

### Limite

Une bande rouge masque le bas de la figure 6-19. La tendance générale et le texte explicatif restent
lisibles, mais aucune valeur précise de cette zone ne doit être transcrite.

### Impact projet

- Le moteur devra afficher séparément variation monétaire et variation relative.
- Une hausse de volatilité ne doit pas être convertie en gain uniforme : strike, maturité et niveau
  initial de volatilité modifient la sensibilité.
- Renforce `R-VOL-001` et prépare la revue du vega.

## Pages imprimées 116–117 — Figures 6-20 et 6-21

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-20 : `Call or Put Vega vs. Time to Expiration`.
- Hypothèses : sous-jacent `100`, volatilité `20 %`.
- Strikes : `90`, `100`, `110`.
- Figure 6-21 : `Call or Put Vega vs. Volatility`.
- Hypothèses : sous-jacent `100`, temps restant `60 jours`.

### Observation documentaire

- Le vega augmente avec le temps restant pour les trois strikes représentés.
- L'option ATM de strike `100` possède le vega le plus élevé sur la figure 6-20.
- À très courte échéance, le vega des options non-ATM tend vers zéro.
- Pour l'option ATM, le vega reste presque constant lorsque le niveau de volatilité change sur la
  figure 6-21.
- Pour les options non-ATM, le vega est presque nul à faible volatilité puis augmente avec la
  volatilité.
- Temps, volatilité et moneyness interagissent donc : « option longue maturité = vega élevé » reste
  incomplet sans le strike et le niveau d'IV.

### Valeurs uniquement indicatives

- Figure 6-20 : à `100 jours`, vegas visuellement proches de `0.22`, `0.15` et `0.12` pour les
  strikes `100`, `110` et `90`.
- Figure 6-21 : le vega ATM reste visuellement proche de `0.16` entre environ `5 %` et `40 %` de
  volatilité.

Ces lectures ne doivent pas servir de calibration.

### Impact projet

- Le moteur devra recalculer le vega à partir de la surface courante, et non utiliser une constante
  par contrat.
- Le risque vega devra être présenté par jambe, maturité et position agrégée.
- Renforce `R-GREEKS-001`, `R-GREEKS-003` et `R-VOL-001`.

## Pages imprimées 118–119 — Figures 6-22 et 6-23

Date de revue : 2026-07-06.

### Contenu vérifié

- Figure 6-22 : `Futures Option Rho vs. Underlying Price`.
- Figure 6-23 : `Stock Option Rho vs. Underlying Price`.
- Hypothèses : strike `100`, volatilité `20 %`, taux d'intérêt `8 %`.
- Maturités : `60` et `150 jours`.
- Sous-jacent représenté approximativement de `80` à `120`.

### Observation documentaire

- Pour les options sur action, le rho des calls est positif et celui des puts négatif.
- La valeur absolue du rho est plus importante à `150 jours` qu'à `60 jours`.
- Sur la figure actions, le rho du call augmente avec le sous-jacent ; le rho du put se rapproche de
  zéro lorsque le sous-jacent augmente.
- La figure des options sur futures présente une structure de rho différente et des valeurs
  négatives pour les calls et puts montrés.
- Les règles de taux ne doivent donc pas être transposées entre options sur actions et options sur
  futures.

### Impact projet

- Le type d'instrument sous-jacent doit être une variable obligatoire du modèle.
- Rho peut rester secondaire pour une option courte, mais ne doit pas être ignoré sur les maturités
  longues.
- Une future intégration IBKR devra distinguer au minimum options sur actions, indices et futures,
  ainsi que leur modèle de valorisation.

### Limite

Les graphes montrent le sens et l'ordre de grandeur dans les hypothèses du livre. Les conventions
exactes de rho et les modèles employés devront être vérifiés avant implémentation.

## Page imprimée 121 — Figure 6-24

Date de revue : 2026-07-06.

### Métadonnées vérifiées

- Date : `22 mai 1992`.
- Modèle : `Black Model`.
- Sous-jacent : deutschemark à `60.71`.
- Temps restant : `105 jours`.
- Volatilité du modèle : `10.5 %`.
- Taux d'intérêt : `4.55 %`.
- Strikes : `52` à `68`.
- Colonnes : prix, valeur théorique, delta, gamma, theta, vega et volatilité implicite.

### Lignes proches de l'ATM transcrites

| Type | Strike | Prix | Théorique | Delta | Gamma | Theta | Vega | IV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Call | 59 | 2.32 | 2.34 | 70 | 10.0 | -0.0053 | 0.111 | 10.3 |
| Call | 60 | 1.72 | 1.72 | 59 | 11.2 | -0.0060 | 0.125 | 10.5 |
| Call | 61 | 1.20 | 1.21 | 47 | 11.5 | -0.0063 | 0.128 | 10.4 |
| Call | 62 | 0.83 | 0.82 | 36 | 10.9 | -0.0059 | 0.121 | 10.6 |
| Put | 59 | 0.64 | 0.65 | -29 | 10.0 | -0.0056 | 0.111 | 10.4 |
| Put | 60 | 1.02 | 1.02 | -40 | 11.2 | -0.0061 | 0.125 | 10.5 |
| Put | 61 | 1.49 | 1.50 | -52 | 11.5 | -0.0062 | 0.128 | 10.4 |
| Put | 62 | 2.11 | 2.09 | -63 | 10.9 | -0.0058 | 0.121 | 10.7 |

### Observation documentaire

- Gamma et vega atteignent leur maximum autour du strike ATM.
- Le gamma est identique pour le call et le put d'un même strike dans ce tableau.
- Le vega est également identique ou quasi identique pour la paire call-put.
- Les deltas call et put reflètent la relation attendue autour de la parité.
- Les volatilités implicites observées varient selon le strike malgré une volatilité de modèle fixée
  à `10.5 %`.

### Limite

Les unités exactes des Greeks doivent être reprises de la convention du modèle avant utilisation.
Les lignes profondes ITM portent des ajustements de parité signalés par une note du livre.

## Page imprimée 122 — Figure 6-25

Date de revue : 2026-07-06.

### Métadonnées vérifiées

- Date : `22 mai 1992`.
- Modèle : `Cox-Ross-Rubenstein`.
- Sous-jacent : General Electric à `76`.
- Volatilité du modèle : `20.5 %`.
- Taux d'intérêt : `4.50 %`.
- Échéances : juin `28 jours`, septembre `119 jours`, décembre `210 jours`.
- Dividende : `0.55` le 3 juin, le 22 septembre et le 3 décembre 1992.
- Strikes : `60`, `65`, `70`, `75`, `80`, `85`.

### Comparaison au strike 75

| Type | Échéance | Prix | Théorique | Delta | Gamma | Theta affiché | Vega | IV |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Call | Juin | 2 3/8 | 2.45 | 67 | 7.9 | 0.037 | 0.073 | 19.0 |
| Call | Septembre | 4 5/8 | 4.38 | 62 | 4.2 | 0.019 | 0.168 | 20.2 |
| Call | Décembre | 6 | 5.58 | 61 | 3.4 | 0.018 | 0.216 | 21.9 |
| Put | Juin | 15/16 | 1.09 | 37 | 7.7 | 0.026 | 0.079 | 18.0 |
| Put | Septembre | 2 7/16 | 2.73 | 40 | 4.5 | 0.011 | 0.169 | 19.3 |
| Put | Décembre | 4 | 3.70 | 41 | 3.3 | 0.006 | 0.219 | 21.4 |

### Observation documentaire

- À strike comparable, le gamma diminue lorsque la maturité s'allonge.
- À l'inverse, le vega augmente fortement avec la maturité.
- Les volatilités implicites diffèrent par strike et par échéance : une IV unique ne décrit pas la
  chaîne complète.
- Le modèle intègre explicitement les dividendes, ce qui rend cette variable obligatoire pour les
  options sur actions.

### Point de convention à résoudre

La figure 6-24 affiche le theta des options longues avec un signe négatif, tandis que la figure 6-25
affiche des valeurs positives. Le texte du chapitre distingue parfois la variation de valeur
théorique et le taux de décroissance du prix. Le futur système ne devra jamais ingérer un champ
`theta` sans enregistrer sa convention de signe et son unité.

La figure 6-25 affiche également les deltas des puts comme des magnitudes positives, alors que la
figure 6-24 utilise des deltas négatifs. La convention de signe du delta doit donc elle aussi être
explicitée.

### Impact projet

- Ces tableaux fournissent des points de contrôle historiques, pas des constantes de production.
- Le moteur devra stocker modèle, date de calcul, taux, dividendes, maturité, strike et convention de
  chaque Greek.
- Renforce `R-GREEKS-001`, `R-GREEKS-002`, `R-GREEKS-003` et le besoin d'une surface d'IV.

## Page imprimée 124 — Figures 6-26 et 6-27

Date de revue : 2026-07-06.

### Conventions de signe vérifiées

| Position | Delta | Gamma | Theta | Vega |
|---|---|---|---|---|
| Long sous-jacent | positif | 0 | 0 | 0 |
| Short sous-jacent | négatif | 0 | 0 | 0 |
| Long call | positif | positif | négatif | positif |
| Short call | négatif | négatif | positif | négatif |
| Long put | négatif | positif | négatif | positif |
| Short put | positif | négatif | positif | négatif |

La figure 6-26 confirme que la figure 6-25 présentait certaines grandeurs comme magnitudes ou taux
de décroissance, et non comme expositions signées prêtes à agréger.

### Interprétation économique vérifiée

- Delta positif : bénéficie d'une hausse du sous-jacent ; delta négatif : d'une baisse.
- Gamma positif : bénéficie d'un mouvement rapide dans l'une ou l'autre direction.
- Gamma négatif : préfère un mouvement lent.
- Theta positif : le passage du temps augmente généralement la valeur de la position.
- Theta négatif : le passage du temps diminue généralement sa valeur.
- Vega positif : bénéficie d'une hausse de volatilité ; vega négatif : d'une baisse.
- Rho positif : bénéficie d'une hausse des taux ; rho négatif : d'une baisse.

Ces formulations décrivent des sensibilités locales, toutes choses égales par ailleurs. Elles ne
garantissent pas le résultat total d'une position.

### Élasticité

La page donne la formule :

`élasticité = (prix du sous-jacent / valeur théorique de l'option) × delta décimal`

Exemple vérifié :

`(50 / 2.50) × 0.25 = 5`

L'élasticité mesure ici le levier relatif : une variation de `2 %` du sous-jacent correspond à une
variation approximative de `10 %` de l'option dans l'exemple local.

### Limite

L'élasticité devient instable lorsque la valeur de l'option est très faible et reste une approximation
locale fondée sur le delta courant.

## Page imprimée 125 — Figure 6-28

Date de revue : 2026-07-06.

### Contenu vérifié

- Tableau individuel de calls et puts aux strikes `90`, `95`, `100`, `105`, `110`.
- Prix, valeur théorique, delta, gamma, theta et vega par option.
- Six positions combinant options et contrats futures.
- Calculs séparés de theoretical edge, delta, gamma, theta et vega de chaque position.

### Exemple d'agrégation clairement lisible

Position :

- long `20` calls strike `100` ;
- short `10` contrats futures.

Résultats affichés :

- theoretical edge : `+1.20` ;
- delta : `+20` ;
- gamma : `+98.0` ;
- theta : `-0.520` ;
- vega : `+3.20`.

Le contrat futures contribue au delta, mais pas au gamma, theta ou vega dans ce tableau.

### Observation documentaire

- Une position presque delta-neutre peut conserver de fortes expositions gamma, theta et vega.
- Une position ne peut donc pas être qualifiée par son seul delta.
- Theoretical edge et risques sont additifs lorsqu'unités, quantités et conventions sont cohérentes.
- Les positions complexes peuvent présenter des signes différents pour chaque dimension de risque.

### Limite

Les multiplicateurs et unités exactes doivent être normalisés avant reproduction. Les autres lignes
du tableau restent des points de contrôle visuel, pas des configurations recommandées.

## Page imprimée 126 — Conclusion du chapitre 6

Date de revue : 2026-07-06.

### Contenu vérifié

- Exemple d'élasticité : `(50 / 2.50) × 0.25 = 5`.
- Valeur théorique et Greeks changent continuellement avec le marché.
- Les Greeks permettent d'identifier les risques ; ils ne les éliminent pas.
- Leur rôle est d'aider à décider quels risques sont acceptables avant la transaction.

### Impact projet

- Le futur moteur devra distinguer mesure du risque, limite acceptée et décision.
- Une exposition calculée ne doit jamais être présentée comme une couverture parfaite.
- La validation utilisateur du budget de risque reste nécessaire avant activation.

## Prochaine page attendue

Pages imprimées 175–176 :

- figures 9-2 et 9-3 ;
- composition exacte des trois spreads et tableau de leurs sensibilités.

Objectif : commencer la comparaison edge/risque des structures multi-jambes.
