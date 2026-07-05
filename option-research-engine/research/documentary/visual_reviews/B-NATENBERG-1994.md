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

## Prochaine page attendue

Page imprimée approximative 108 :

- `Figure 6-10: Call or Put Gamma vs. Volatility`.

Objectif : vérifier comment le gamma ATM et non-ATM évolue lorsque l'hypothèse de volatilité change.
