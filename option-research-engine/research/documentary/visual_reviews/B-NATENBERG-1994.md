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

## Prochaine page attendue

Page imprimée approximative 113 :

- `Figure 6-17: Call or Put Theta vs. Time to Expiration`.

Objectif : vérifier la forme de l'accélération du theta selon la moneyness à l'approche de
l'expiration.
