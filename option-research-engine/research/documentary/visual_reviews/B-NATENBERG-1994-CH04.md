# Revue visuelle — B-NATENBERG-1994 — Chapitre 4

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Chapitre : 4 — Volatility.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
valeurs utiles et limites contrôlées visuellement. Les conclusions restent documentaires : aucune
règle n'est active pour trading ou exécution IBKR.

## Distribution, volatilité et valeur d'option — pages 52–56, figures 4-1 à 4-5

### Figures 4-1 et 4-2

Les premières figures utilisent une marche aléatoire et une distribution en cloche pour montrer que
les résultats les plus probables se concentrent près du centre, tandis que les résultats extrêmes
sont moins fréquents.

### Figures 4-3 à 4-5

Les distributions low, moderate et high volatility montrent que :

- une distribution basse volatilité est étroite, avec peu de probabilité d'atteindre un strike OTM ;
- une distribution haute volatilité est plus large, donc donne plus de probabilité aux résultats
  extrêmes ;
- pour une option, seuls les résultats dans la monnaie comptent réellement pour sa valeur ;
- une hausse de volatilité augmente la valeur d'une option car la perte de l'acheteur est limitée
  mais l'upside peut devenir important.

### Impact projet

Le moteur doit traiter la volatilité comme une hypothèse de dispersion des prix, pas comme un simple
label `haut/bas`. Une option OTM peut devenir beaucoup plus sensible à la volatilité qu'une lecture
du prix brut ne le suggère.

## Moyenne, écart-type et probabilités — pages 56–59, figure 4-6

Le chapitre rappelle qu'une distribution normale est décrite par :

- une moyenne ;
- un écart-type.

Repères contrôlés :

| Distance à la moyenne | Approximation |
|---|---:|
| ±1 écart-type | 68.3 % |
| ±2 écarts-types | 95.4 % |
| ±3 écarts-types | 99.7 % |

Exemple de la figure 4-6 :

- moyenne : `7.50` ;
- écart-type : `3.00` ;
- `±1` écart-type : de `4.50` à `10.50` ;
- `±2` écarts-types : de `1.50` à `13.50`.

### Impact projet

Ces repères servent à produire des stress ranges compréhensibles :

- mouvement journalier attendu ;
- mouvement hebdomadaire attendu ;
- probabilité approximative d'un mouvement extrême ;
- distance entre le strike et la distribution attendue.

Le moteur ne doit pas présenter ces probabilités comme exactes : elles reposent sur une hypothèse
de distribution et sur une estimation de volatilité.

## Prix forward comme moyenne — page 60

Le chapitre distingue le prix spot du centre de distribution utilisé par le modèle :

- futures sans carry/dividende : le prix de break-even futur peut être le prix de trade ;
- actions : le forward dépend des coûts de portage, taux et dividendes.

Exemple visible :

- action `100` ;
- taux annuel `8 %` ;
- trois mois de portage : environ `2` ;
- dividende `1` ;
- break-even ajusté : `101` au lieu de `102`.

### Impact projet

Le modèle doit utiliser un forward cohérent avec le type de sous-jacent. Comparer des options sans
taux/dividendes peut fausser le centre de distribution et donc l'edge.

## Volatilité comme écart-type annualisé — pages 60–61

Définition documentaire : la volatilité est utilisée comme changement de prix d'un écart-type, en
pourcentage, sur une période d'un an.

Exemples visibles :

- futures à `100`, volatilité `20 %` :
  - intervalle `±1σ` : `80` à `120` ;
  - intervalle `±2σ` : `60` à `140` ;
  - intervalle `±3σ` : `40` à `160`.
- action à `100`, taux `8 %`, sans dividende :
  - forward un an `108` ;
  - `1σ = 20 % × 108 = 21.60` ;
  - intervalle `±1σ` : `86.40` à `129.60`.

Le texte avertit qu'un événement au-delà de trois écarts-types est improbable mais pas impossible.
Une seule observation extrême ne suffit pas à invalider mécaniquement l'estimation de volatilité ; il
faut regarder une distribution représentative.

## Lognormalité et hypothèses Black-Scholes — pages 61–65, figure 4-7

Le chapitre explique pourquoi une distribution normale des prix pose un problème : elle autorise des
prix négatifs. La distribution lognormale évite ce problème :

- les prix sont bornés par zéro côté baisse ;
- les prix restent ouverts côté hausse ;
- les rendements en pourcentage sont traités comme normalement distribués ;
- les prix à expiration deviennent lognormalement distribués.

Hypothèses résumées page 64 :

1. les changements de prix sont aléatoires ;
2. les changements en pourcentage sont normalement distribués ;
3. avec composition continue, les prix à expiration sont lognormalement distribués ;
4. la moyenne de la distribution lognormale est située au forward.

### Limite documentaire

Natenberg signale que ces hypothèses peuvent être raisonnables sur certains marchés et faibles sur
d'autres. Le trader doit comprendre sur quelles hypothèses reposent ses valeurs théoriques.

### Impact projet

Le futur outil devra stocker le modèle et ses hypothèses, pas seulement le résultat. Un écart
modèle/marché peut venir de l'hypothèse de distribution, pas seulement du prix d'une option.

## Écart-type journalier et hebdomadaire — pages 65–66

Le chapitre utilise la règle de racine carrée du temps :

```text
volatilité_période ≈ volatilité_annuelle / sqrt(nombre_de_périodes)
```

Approximation pratique :

- `256` jours de trading, racine `16` ;
- `52` semaines, racine approximative `7.2`.

Exemples visibles :

- futures `100`, vol annuelle `20 %` :
  - vol quotidienne : `20 % / 16 = 1.25 %`, soit `1.25` point ;
  - vol hebdomadaire : `20 % / 7.2 ≈ 2.75 %`, soit `2.75` points.
- action `45`, vol annuelle `28 %` :
  - mouvement `1σ` quotidien : `28 % / 16 × 45 = 0.79` ;
  - mouvement `1σ` hebdomadaire : `28 % / 7.2 × 45 = 1.75`.

Le texte précise que la mesure traditionnelle utilise les changements settlement-to-settlement, pas
nécessairement high/low ou open/close.

### Impact projet

Pour comparer IV, volatilité réalisée et risques de hedge, le moteur doit rendre explicite :

- annualisation utilisée ;
- nombre de périodes ;
- source du prix de référence ;
- settlement-to-settlement vs intraday range.

## Volatilité observée et cohérence des mouvements — pages 67–68

Natenberg montre comment vérifier si les mouvements observés sont cohérents avec une volatilité
supposée.

### Exemple 1

- sous-jacent `40` ;
- vol utilisée `30 %` ;
- mouvement quotidien `1σ ≈ 30 % / 16 × 40 = 0.75` ;
- changements observés sur 5 jours : `+0.43`, `-0.06`, `-0.61`, `+0.50`, `-0.28`.

Conclusion documentaire : ces cinq jours ne sont pas cohérents avec une volatilité de `30 %`; la
volatilité réalisée implicite de l'exemple est indiquée à `18.8 %`. Le texte avertit cependant que
cinq jours est un petit échantillon.

### Exemple 2

- sous-jacent `332 1/2` ;
- vol supposée `18 %` ;
- mouvement quotidien `1σ ≈ 3 3/4` ;
- changements observés : `-5`, `+2 1/2`, `+1`, `-7 3/4`, `-4 1/4`.

Conclusion documentaire : plusieurs mouvements excèdent `1σ`, dont un mouvement supérieur à `2σ`.
Sauf semaine extraordinaire, il faut envisager d'ajuster l'entrée de volatilité.

### Impact projet

Le moteur devra comparer la volatilité utilisée aux mouvements observés, mais avec une prudence
d'échantillon :

- ne pas recalibrer une volatilité sur cinq jours sans contexte ;
- signaler une incohérence entre mouvements réalisés et hypothèse ;
- distinguer événement exceptionnel et régime de volatilité différent.

## Produits de taux et conventions spéciales — pages 68–69

Les Eurodollars et certains produits de taux peuvent nécessiter une transformation :

- prix indexé à `100` ;
- valeur économique modélisée comme `100 - prix coté` ;
- calls/puts cotés peuvent être inversés dans le modèle ;
- distinction entre price volatility et yield volatility.

### Impact projet

Le moteur IBKR ne doit pas supposer que toutes les options utilisent la même convention de
sous-jacent. Les produits de taux exigent des conventions spécifiques avant tout calcul d'IV, Greeks
ou edge.

## Types de volatilité — pages 69–75

### Future volatility

La volatilité future est la vraie volatilité qui décrira la distribution future. C'est l'entrée
idéale du modèle, mais elle est inconnue.

### Historical volatility

La volatilité historique est un point de départ, pas une réponse finale. Elle dépend :

- de la période historique choisie ;
- de l'intervalle entre observations ;
- du régime de marché.

Le texte indique qu'une plage historique peut aider à rejeter des estimations absurdes, tout en
rappelant que les extrêmes restent possibles.

### Forecast volatility

La volatilité forecast est une estimation prospective. Elle peut être produite par un service ou par
le trader, mais reste inexacte.

### Implied volatility — pages 72–75, figure 4-9

L'IV est la volatilité qui rend la valeur théorique égale au prix de marché observé, toutes les
autres entrées étant tenues constantes.

Exemple visible :

- futures `98.50` ;
- call `105` ;
- temps `3 mois` ;
- taux `8 %` ;
- vol initiale `16 %` ;
- valeur théorique `0.96` ;
- prix marché `1.34` ;
- IV résolue : `18.5 %`.

La figure 4-9 distingue :

- modèle en mode pricing : entrées connues, valeur théorique inconnue ;
- modèle en mode IV : prix connu, volatilité inconnue.

### Limites de l'IV

L'IV dépend :

- du modèle utilisé ;
- de l'exactitude des autres entrées ;
- de la fraîcheur du prix de l'option ;
- de la fraîcheur du sous-jacent ;
- de la liquidité.

Exemple textuel : si le prix de l'option vient d'un trade ancien alors que le sous-jacent a bougé,
l'IV calculée peut changer fortement.

### Valeur vs prix

Le chapitre formule la relation centrale :

- future volatility détermine la valeur ;
- implied volatility reflète le prix.

Pour un trader, cela revient à comparer volatilité future estimée et volatilité implicite.

### Impact projet

Le moteur devra toujours conserver :

- IV par option ;
- modèle utilisé ;
- timestamp du prix option ;
- timestamp du sous-jacent ;
- entrées de taux/dividendes ;
- méthode d'agrégation IV si une IV unique est affichée.

Un écart `forecast IV - implied IV` ne suffit pas sans vérifier la qualité des entrées.

## Saisonnalité et sensibilité à la volatilité — pages 76–79, figures 4-10 à 4-12

### Figure 4-10 — soja

La volatilité saisonnière peut rendre certains mois structurellement plus volatils. Dans l'exemple
du soja, juin-juillet-août affichent des niveaux de volatilité beaucoup plus élevés que certains
mois de printemps.

### Figure 4-11 — options or

La table montre des valeurs théoriques pour des options or à différents strikes sous trois
hypothèses de volatilité : `11 %`, `14 %`, `17 %`.

Enseignements :

- les options ATM changent fortement en valeur lorsque la vol passe de `11` à `14` puis `17 %` ;
- certaines options OTM peuvent plus que doubler en valeur en pourcentage lorsque la volatilité
  augmente ;
- une variation de `3` points de volatilité sur dix semaines n'est pas inhabituelle dans l'exemple.

### Figure 4-12 — or

La figure montre que la volatilité historique sur dix semaines de l'or varie fortement dans le temps,
avec des épisodes autour de `10 %` et d'autres proches de `26–28 %`.

### Conclusion page 79

Le chapitre conclut qu'il faut choisir des stratégies rentables si l'estimation de volatilité est
correcte, mais qui ne produisent pas une perte désastreuse si elle est fausse. Il avertit qu'une
marge d'erreur d'un point de volatilité n'est pas une marge suffisante dans un marché où la
volatilité peut passer de `15 %` prévu à `16 %` réalisé.

### Impact projet

La future sélection de structures doit inclure :

- marge d'erreur de volatilité ;
- scénarios saisonniers si le sous-jacent l'exige ;
- stress de plusieurs points de volatilité ;
- test de perte désastreuse si l'estimation est fausse.

## Conclusions provisoires pour Take Two

1. La volatilité est une hypothèse de dispersion des prix, pas une direction.
2. Les options réagissent à la dispersion parce que la perte de l'acheteur est bornée.
3. Le modèle doit utiliser un forward cohérent avec le sous-jacent.
4. L'annualisation et la racine carrée du temps doivent être explicites.
5. L'IV est un prix traduit en volatilité, pas une prévision pure.
6. Historical, forecast, future et implied volatility doivent rester séparées.
7. Un écart forecast/IV ne suffit pas si les inputs ou timestamps sont mauvais.
8. Une marge d'erreur d'un point de volatilité peut être insuffisante.
9. Les produits de taux et matières premières peuvent exiger des conventions/saisonnalités
   spécifiques.
10. Le futur script IBKR doit stresser la volatilité avant de préférer une structure.

## Prochaine page attendue

Chapitre 5 :

- theoretical value ;
- edge ;
- comparaison prix marché vs valeur théorique ;
- delta hedge et maintenance de position ;
- tout tableau/figure liant valeur théorique, edge et Greeks.
