# Revue visuelle — B-MCMILLAN-2012 — Chapitre 3

Source : Lawrence G. McMillan, *Options as a Strategic Investment*, 5e édition.

Chapitre : 3 — Call Buying.

Statut : `in_progress`

Date de revue : 2026-07-06.

Périmètre reçu : chapitre complet, pages imprimées `97–117` (pages PDF `121–141`).

Les images du livre ne sont pas versionnées. Cette fiche conserve les mécanismes, exemples et
limites contrôlés visuellement. Les conclusions restent documentaires : aucune règle n'est active
pour trading ou exécution IBKR.

## Risque et rendement de l'acheteur de call — pages 97–98

McMillan place d'abord la sélection du sous-jacent avant celle du contrat. Une bonne anticipation
directionnelle peut néanmoins perdre si le strike ou l'échéance sont mal choisis.

### Moneyness

- Un call OTM est moins cher et offre un rendement en pourcentage potentiellement plus élevé si le
  sous-jacent monte fortement.
- Il présente aussi une probabilité supérieure de perte totale.
- Un call ITM coûte davantage, mais suit mieux une hausse modérée et présente moins de risque
  d'expirer sans valeur.
- Le prix absolu le plus faible ne doit donc pas être utilisé seul pour choisir le call.

Exemple visible page 97 :

- sous-jacent `XYZ = 65` ;
- call juillet `60` coté `7` ;
- call juillet `70` coté `3`.

À `XYZ = 68`, le call `60` conserve au moins `8` de valeur intrinsèque, tandis que le call `70`
peut encore expirer sans valeur. McMillan résume le compromis ainsi : l'ITM convient mieux à une
hausse modeste ; l'OTM exige une hausse plus forte mais peut produire un rendement supérieur.

### Échéance et certitude du timing

- Une échéance éloignée réduit le risque lié à une erreur de timing, mais son coût supplémentaire
  peut devenir inutile pour un trade censé être rapide.
- Lorsque le mouvement est attendu immédiatement et que le timing paraît fiable, McMillan envisage
  un call court terme légèrement OTM.
- Lorsque le timing est incertain mais que la thèse directionnelle reste valable, une échéance plus
  longue laisse davantage de temps à la thèse.

### Impact projet

Le moteur ne doit jamais classer les calls uniquement par prime ou levier. Il doit relier :

- amplitude attendue du mouvement ;
- confiance dans le timing ;
- durée prévue de détention ;
- moneyness et delta ;
- risque de perte totale.

## Delta et courbes de prix — pages 99–101, figure 3-1

McMillan définit ici le delta comme la variation approximative du prix du call pour un mouvement
d'un point du sous-jacent.

### Figure 3-1

La figure compare les courbes de prix de calls à `3`, `6` et `9` mois :

- près du strike, la valeur temps est la plus élevée ;
- loin ITM ou OTM, elle diminue ;
- à l'approche de l'expiration, la courbe rejoint progressivement la valeur intrinsèque ;
- le delta est représenté par la pente locale de la courbe et change donc avec le sous-jacent.

Exemples visibles :

- call profondément ITM : delta proche de `1` ;
- call profondément OTM : delta proche de `0` ;
- call ATM : delta souvent situé approximativement entre `0.50` et `0.625` dans l'exemple
  pédagogique.

McMillan distingue explicitement :

- le delta instantané, qui change avec le marché ;
- le `dollar delta`, soit la variation effective du prix de l'option pour le mouvement observé.

### Comparaison page 101

Situation :

- `XYZ = 47½` ;
- call juillet `45` : prix `3½`, delta `5/8` ;
- call juillet `50` : prix `1`, delta `1/4`.

Pour une hausse rapide vers `49`, le call `45` gagne davantage en dollars, mais le call `50` gagne
davantage en pourcentage dans l'exemple, avant commissions.

### Impact projet

Le moteur doit distinguer :

- gain absolu attendu ;
- rendement en pourcentage ;
- probabilité d'atteindre la zone rentable ;
- commissions et bid-ask ;
- delta courant, qui ne doit pas être traité comme constant sur tout le scénario.

## Quel call acheter ? — pages 101–103

McMillan relie le choix à l'horizon de la stratégie.

| Horizon | Orientation documentaire |
|---|---|
| Day trading | privilégier le sous-jacent ; si une option est utilisée, call court terme ITM à delta élevé, proche de `0.90` |
| Court terme, environ une à deux semaines | call court terme ITM à delta élevé |
| Intermédiaire | échéance plus longue et strike proche de l'ATM pour limiter le risque de timing |
| Long terme | call légèrement OTM ou au moins correctement ITM ; LEAPS éventuellement plus adaptés |

Ces orientations ne sont pas encore des règles actives : le texte ne chiffre pas ici les coûts,
spreads de marché, liquidité minimale ni conditions d'exception.

## Critères avancés — pages 103–105

McMillan avertit qu'un classement de calls fondé seulement sur la variation en pourcentage du
sous-jacent est trompeur. Les classements doivent tenir compte de la volatilité du sous-jacent :
un call sur une action volatile est naturellement plus cher qu'un call comparable sur une action
peu volatile.

### Impact projet

Une comparaison inter-sous-jacents doit être normalisée par la volatilité. Le moteur ne doit pas
confondre prime élevée et surévaluation sans comparer la volatilité implicite, la volatilité
attendue et le risque propre au sous-jacent.

### Comparaison normalisée par volatilité

McMillan compare deux actions à `40` :

- `NVS`, peu volatile, call juillet `40` coté `2` ;
- `VVS`, volatile, call juillet `40` coté `4`.

Une hausse identique de `10 %` donnerait apparemment l'avantage au call NVS. Cette comparaison est
rejetée car elle suppose que les deux sous-jacents ont la même probabilité de progresser de `10 %`.

Lorsque le mouvement est adapté à la volatilité propre de chaque action :

- VVS peut progresser de `15 %`, de `40` à `46`, et son call de `4` à `6`, soit `+50 %` ;
- NVS peut progresser de `5 %`, de `40` à `42`, et son call reste environ à `2`.

Sur un horizon réaliste de `90` jours, l'exemple conserve VVS comme meilleur achat, mais avec des
gains estimés plus modestes :

- VVS : action `40 → 44.8`, call `4 → 6`, soit `+50 %` ;
- NVS : action `40 → 41.6`, call `2 → 2½`, soit `+25 %`.

### Procédure de classement décrite page 105

1. Fixer un horizon, par exemple `30`, `60` ou `90` jours.
2. Estimer une hausse cohérente avec la volatilité du sous-jacent.
3. Estimer le prix du call après cette hausse.
4. Classer les calls selon leur rendement potentiel.
5. Estimer ensuite une baisse cohérente avec la volatilité.
6. Estimer le prix du call après cette baisse.
7. Classer les calls par ratio rendement/risque : gain estimé divisé par perte estimée.

Le premier classement favorise les achats agressifs. Le ratio rendement/risque produit une
sélection plus conservatrice. McMillan précise aussi que le delta intervient indirectement dans ces
estimations.

### Limites

- L'horizon retenu doit correspondre à la durée réelle de détention, pas automatiquement à
  l'expiration.
- Le calcul nécessite des estimations de volatilité et de prix futurs qui restent incertaines.
- Les commissions doivent être incluses.
- Les résultats sont présentés comme impossibles à établir proprement sans calcul informatique.

## Calls surévalués ou sous-évalués — page 106

McMillan définit :

- un call surévalué comme un call coté au-dessus de sa valeur « juste » calculée ;
- un call sous-évalué comme un call coté en dessous.

Il avertit toutefois qu'une sous-évaluation ne suffit pas, à elle seule, à rendre l'achat
intéressant :

- les écarts observés peuvent être très faibles ;
- le market maker peut capter une partie de l'écart ;
- commissions et coûts de transaction peuvent absorber l'avantage ;
- un call bon marché qui a déjà chuté n'est pas nécessairement une bonne affaire.

Si tous les calls sont surévalués, McMillan évoque l'ajout d'un put à l'achat du call comme piste de
réduction du coût, mais renvoie l'étude détaillée à un chapitre ultérieur.

### Impact projet

Le moteur doit calculer un `edge net` après bid-ask, commissions et coûts estimés. Le statut
`undervalued` ne doit jamais déclencher seul une entrée.

## Valeur temps et frustrations de l'acheteur — pages 106–107

McMillan qualifie l'expression `time value premium` de trompeuse : la valeur non intrinsèque ne
dépend pas seulement du temps, mais fortement de la volatilité anticipée. Une révision brutale des
anticipations de volatilité peut modifier le prix du call bien avant que le temps ne se soit
écoulé.

Les frustrations de l'acheteur proviennent de l'interaction entre :

- delta ;
- dégradation temporelle ;
- volatilité du sous-jacent.

## Follow-Up Action — pages 107–111

### Sortie en perte

McMillan recommande de sortir lorsque le sous-jacent invalide le scénario :

- ne pas conserver le call uniquement dans l'espoir d'un rebond ;
- définir le stop à partir du comportement technique du sous-jacent, pas du seul prix de l'option ;
- utiliser un ordre réellement exécutable plutôt qu'un simple `mental stop` lorsque cela est
  approprié.

### Prise partielle de profits

Une position gagnante peut être réduite partiellement :

- vendre une partie pour récupérer la mise ou matérialiser un profit ;
- conserver le solde pour participer à une poursuite de la hausse ;
- accepter les gains sur le contrat cher avec la même discipline que sur un contrat initialement
  peu coûteux.

McMillan note aussi que vendre le call est souvent économiquement préférable à son exercice lorsque
les commissions sur actions sont supérieures aux commissions sur options.

## Verrouillage des profits — pages 108–111, tableaux 3-1 à 3-3

Exemple initial :

- `XYZ = 48` ;
- achat du call octobre `50` à `3` ;
- après hausse, `XYZ = 58` ;
- call octobre `50 = 9` ;
- call octobre `60 = 3`.

Quatre choix sont comparés :

1. liquider le call ;
2. `roll up` : vendre le call `50` et acheter plusieurs calls `60` ;
3. créer un bull spread : conserver le call `50` et vendre le call `60` ;
4. ne rien faire.

### Lecture des tableaux

- La liquidation verrouille `6` points, mais abandonne toute hausse future.
- Ne rien faire conserve le potentiel maximal, mais peut rendre tout le gain non réalisé.
- Le `roll up` récupère la mise initiale et remplace la position par davantage de calls OTM. C'est
  l'alternative la plus agressive et elle exige une hausse substantielle.
- Le bull spread plafonne le gain, mais n'est jamais la pire des quatre tactiques dans les scénarios
  du tableau 3-3. Il est favorisé lorsque le sous-jacent reste relativement stable au-dessus du
  strike bas sans monter fortement au-delà du strike haut.

La table 3-2 résume notamment :

| Scénario futur | Meilleure tactique | Pire tactique |
|---|---|---|
| hausse spectaculaire | `roll up` | liquidation |
| hausse modérée au-dessus du strike suivant | ne rien faire | liquidation ou `roll up` |
| stabilité relative | spread | `roll up` |
| baisse sous le strike initial | liquidation | ne rien faire |

McMillan précise qu'aucune tactique n'est universellement meilleure. Une réduction partielle de la
position peut combiner récupération de capital et participation résiduelle.

### Impact projet

Le moteur doit comparer les actions de maintenance sur une grille de scénarios, pas sélectionner
une action uniquement parce qu'elle maximise le gain possible :

- baisse ;
- stabilité ;
- hausse modérée ;
- hausse forte ;
- coûts et liquidité ;
- capital libéré ou réinvesti.

## Defensive Action — rolling down — pages 112–116, tableaux 3-4 et 3-5, figure 3-2

McMillan décrit une défense d'un call en perte par transformation en bull spread :

- vendre `2` calls du strike détenu ;
- acheter `1` call au strike inférieur ;
- chercher une opération proche de coût nul, ou à faible débit.

Exemple :

- achat initial d'un call octobre `35` à `3`, avec `XYZ = 35` ;
- après baisse : `XYZ = 32`, call octobre `35 = 1½`, call octobre `30 = 3` ;
- vente de `2` calls `35` et achat de `1` call `30`.

Position finale :

- long `1` call `30` ;
- short `1` call `35` ;
- coût initial conservé : environ `$300`, avant commissions.

Effets illustrés :

- break-even abaissé d'environ `38` à `33` lorsque le roll est sans coût ;
- prix du sous-jacent déclenchant la perte maximale abaissé de `35` à `30` ;
- perte maximale nominale inchangée dans l'exemple sans débit ;
- potentiel de profit plafonné à l'écart entre strikes moins le coût.

Avec un débit supplémentaire de `$100` :

- break-even autour de `34` ;
- perte maximale augmentée ;
- profit maximal réduit à environ `$100`, avant commissions.

### Limites

- Le `rolling down` augmente la probabilité de récupération seulement si le sous-jacent rebondit
  suffisamment.
- Il sacrifie le potentiel de hausse du call initial.
- Il peut rester préférable à un `average down`, car il abaisse le break-even avec moins de capital
  additionnel, mais cette comparaison dépend des prix disponibles.
- Commissions et possibilité réelle d'exécution peuvent éliminer l'intérêt.

## Calendar spread défensif — pages 116–117

Autre défense évoquée :

- conserver un call intermédiaire ou long terme en perte ;
- vendre un call court terme au même strike ;
- utiliser la prime reçue pour diminuer le coût de la position.

McMillan avertit explicitement que cette défense peut perdre des deux côtés si le sous-jacent
remonte rapidement avant l'échéance courte. Elle doit donc être utilisée avec grande prudence.

## Marge et faisabilité — page 117

Avant toute transformation en spread, l'acheteur doit vérifier :

- règles de marge de l'exchange et du courtier ;
- type de compte ;
- capital minimal ;
- restrictions propres au spread ;
- possibilité réelle de roll.

Un call long ne doit pas être supposé automatiquement transformable en spread.

## Conclusion documentaire du chapitre

Le chapitre fournit trois familles de décisions distinctes :

1. sélection initiale : horizon, volatilité, moneyness, delta et ratio rendement/risque ;
2. maintenance d'une position gagnante : liquidation, réduction partielle, `roll up`, spread ou
   maintien ;
3. défense d'une position perdante : liquidation, `rolling down` ou calendar spread prudent.

Ces choix exigent une évaluation par scénarios et un edge net de coûts. Ils restent
`documentary_candidates` jusqu'à validation quantitative et décision explicite.
