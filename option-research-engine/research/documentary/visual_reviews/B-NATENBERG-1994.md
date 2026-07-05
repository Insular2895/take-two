# Revue visuelle — B-NATENBERG-1994

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Statut : `in_progress`

Méthode : contrôle page par page à partir d'images fournies par l'utilisateur. Les images du livre
ne sont pas versionnées. Seuls les identifiants de figures, hypothèses visibles, observations et
limites sont conservés.

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

## Prochaine page attendue

Page imprimée 116 :

- `Figure 6-20: Call or Put Vega vs. Time to Expiration`.

Objectif : vérifier comment la maturité et la moneyness modifient la sensibilité à la volatilité.
