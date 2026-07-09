# Revue visuelle — B-NATENBERG-1994 — Chapitre 13

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Chapitre : 13 — Hedging with Options.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
équivalences synthétiques, valeurs utiles et limites contrôlées visuellement. Les conclusions
restent documentaires : aucune règle n'est active pour trading ou exécution IBKR.

## Objectif du chapitre — pages 257–258

Le chapitre traite l'option comme un instrument d'assurance partielle, contrairement au futur qui
transfère plus directement le risque d'une partie à une autre.

### Points contrôlés

- Les hedgers peuvent être des `natural longs` ou des `natural shorts`.
- Un hedge a toujours un coût : prime explicite, opportunité de profit abandonnée ou risque
  additionnel.
- Toute décision de hedge est un arbitrage entre protection, coût, upside conservé et risque
  résiduel.

### Impact projet

Le futur moteur ne doit pas classifier un hedge uniquement comme `protégé` ou `non protégé`. Il doit
afficher :

- risque éliminé ;
- risque conservé ;
- coût explicite ;
- upside abandonné ;
- risque nouveau introduit par la structure.

## Protective calls and puts — pages 258–260, figures 13-1 et 13-2

### Construction

- Achat d'un call pour protéger une position short sous-jacent.
- Achat d'un put pour protéger une position long sous-jacent.
- Le strike joue le rôle de franchise d'assurance : protection plus proche = coût plus élevé.

### Exemple Deutschemark

Une firme américaine attend une livraison de biens allemands et se retrouve exposée à une hausse du
Deutschemark contre dollar. Elle peut acheter un call Deutschemark pour plafonner son coût d'achat
effectif.

Exemples de coût visibles :

- call `.64` à `.0075` sur `1,000,000` DM : coût `7,500`.
- call `.66` à `.0025` : coût `2,500`, mais protection seulement au-dessus de `.66`.
- call `.62` à `.015` : coût `15,000`, mais protection plus forte.

### Équivalences synthétiques

Le chapitre donne explicitement :

- `short underlying + long call = long put`
- `long underlying + long put = long call`

### Profil

- Risque adverse limité par le strike choisi.
- Profit favorable conservé au-delà de la prime payée.
- Coût certain sous forme de prime.

### Limite visuelle

Une bande rouge masque la partie basse de la figure 13-2. Le profil général du protective put reste
lisible, mais aucune valeur verticale précise n'est transcrite.

### Impact projet

Le moteur doit permettre de comparer plusieurs strikes de protection en montrant simultanément :

- prime payée ;
- perte maximale après hedge ;
- seuil à partir duquel la protection commence ;
- participation restante au scénario favorable.

## Covered writes — pages 260–263, figures 13-3 et 13-4

### Construction

- Covered call : long sous-jacent + vente d'un call.
- Covered put : short sous-jacent + vente d'un put.
- La vente d'option fournit un crédit mais ne donne pas la même protection bornée qu'une option
  protectrice achetée.

### Exemple covered call

Sous-jacent à `100` :

- vendre le call `95` à `6 1/2` protège davantage la baisse, mais abandonne quasiment tout upside
  au-dessus de `95`.
- vendre le call `105` à `2` protège seulement une baisse de `2` points, mais laisse participer à la
  hausse jusqu'à `105`.

### Équivalences synthétiques

Le chapitre donne explicitement :

- `long underlying + short call = short put`
- `short underlying + short put = short call`

### Critère théorique de choix

Natenberg relie le choix protecteur vs covered write à `price versus value` :

- si l'option est moins chère que sa valeur, l'achat protecteur devient plus logique ;
- si l'option est plus chère que sa valeur, la vente couverte devient plus logique ;
- en pratique, le strike dépend aussi du risque que le hedger accepte et de l'upside qu'il veut
  conserver.

### Impact projet

Pour Take Two, un covered call ne doit pas être présenté comme une simple stratégie de rendement. Il
doit être vu comme une transformation synthétique en short put, avec :

- downside conservé ;
- upside plafonné ;
- prime reçue ;
- risque d'assignation ;
- comparaison IV observée vs volatilité prévue.

## Fences / collars — pages 263–265, figures 13-5 et 13-6

### Construction

Un fence combine :

- achat d'une option protectrice ;
- vente d'une option couverte.

Pour une position long sous-jacent, l'exemple est :

- acheter un put `45` ;
- vendre un call `55`.

Si le put `45` vaut `1.25` et le call `55` vaut `1.75`, le hedge est établi pour un crédit de
`.50`, ce qui réduit le prix de revient effectif du sous-jacent à `49.50` dans l'exemple.

### Équivalence synthétique

Le chapitre montre qu'un long fence est équivalent à un bull vertical spread synthétique :

- `long 45 put = short underlying + long 45 call`
- `45/55 fence = long underlying + long 45 put + short 55 call`
- donc `45/55 fence = long 45 call + short 55 call`

Un short fence est équivalent à un bear vertical spread.

### Noms équivalents

Le chapitre note que les fences sont aussi appelés :

- range forwards ;
- tunnels ;
- cylinders ;
- split-price conversions and reversals.

En taux, le même principe devient un `collar` :

- borrower : acheter un cap et vendre un floor ;
- lender : acheter un floor et vendre un cap.

### Impact projet

Le moteur doit traiter collars/fences comme des bornes explicites de scénario :

- floor de perte ou de coût ;
- cap d'upside ;
- coût net ou crédit ;
- équivalence spread vertical ;
- risque que le zéro-cost hedge cache une forte concession d'upside.

## Complex hedging strategies — pages 265–268

### Questions de décision

Le chapitre propose trois questions préalables :

1. Le hedge doit-il protéger contre un scénario `worst case` ?
2. Quelle part du risque directionnel actuel doit être éliminée ?
3. Quels risques additionnels le hedger accepte-t-il ?

### Règle qualitative IV haute / IV basse

Natenberg formule une règle générale :

- en IV haute, acheter aussi peu d'options que possible et en vendre autant que possible ;
- en IV basse, acheter autant d'options que possible et en vendre aussi peu que possible.

### Delta comme quantité de protection

Exemple : pour couvrir `50 %` d'une position long sous-jacent, le hedger peut viser un total delta
de puts de `-50` :

- un put ATM delta `-50` ;
- ou plusieurs puts OTM dont les deltas s'additionnent à `-50`.

En IV haute, le chapitre préfère souvent acheter moins d'options : par exemple un put delta `-50`
plutôt que plusieurs puts OTM totalisant `-50`.

### Avertissement sur ratios et vente excessive

Vendre plusieurs calls contre une seule position long sous-jacent peut transformer un hedge en
position à risque illimité à la hausse. Natenberg avertit qu'un true hedger doit garder son objectif
principal : protéger une position existante et garder le coût de protection aussi bas que possible,
sans oublier les risques créés.

### Spreads comme hedges partiels

Le chapitre propose d'utiliser :

- time spreads ;
- butterflies ;
- vertical spreads ;

pour atteindre un delta de protection donné tout en choisissant une exposition à la volatilité.

Exemples visibles :

- IV basse et short sous-jacent à `100` : acheter un `110` call time spread avec delta positif ;
- si le spread a delta `+25`, acheter deux spreads pour couvrir `50 %` d'un short sous-jacent ;
- IV haute : vendre un time spread de strike plus bas, avec delta positif et edge théorique positif ;
- long sous-jacent à `100` : vendre un vertical call spread avec delta négatif pour protéger la
  baisse.

### Impact projet

Le futur moteur doit séparer :

- objectif de hedge directionnel ;
- opinion sur volatilité ;
- contrainte de risque maximal ;
- risque de ratio ou d'exposition non couverte ;
- budget de coût ou de crédit.

Le résultat ne doit pas être une stratégie unique, mais une shortlist limitée de structures avec
profils risk/reward comparables.

## Figure 13-7 — Summary of Hedging Strategies — page 269

La figure compare des stratégies selon position long/short, avantage et désavantage.

### Long underlying

| Stratégie | Avantage principal | Désavantage principal |
|---|---|---|
| Buy a protective put | downside limité ; upside illimité ; edge potentiel positif | edge potentiel négatif |
| Sell a covered call | edge potentiel positif | downside illimité ; upside limité |
| Long fence | downside limité | edge potentiel négatif |
| Ratio put purchase | upside illimité ; downside partiellement limité | dette possible si prix put > prix call |
| Ratio call write | edge potentiel positif | downside illimité ; upside illimité si survente |
| Bear vertical spread | edge potentiel positif | downside illimité |
| Bear time spread | downside illimité | edge potentiel négatif |

### Short underlying

| Stratégie | Avantage principal | Désavantage principal |
|---|---|---|
| Buy a protective call | upside limité ; downside illimité favorable | edge potentiel négatif |
| Sell a covered put | edge potentiel positif | upside illimité |
| Short fence | upside limité ; downside favorable limité | edge potentiel négatif |
| Ratio call purchase | downside favorable illimité ou limité ; upside partiellement limité | débit possible si prix call > prix put |
| Ratio put write | edge potentiel positif | upside illimité ; downside illimité si survente |
| Bull vertical spread | edge potentiel positif | upside illimité |
| Bull time spread | edge potentiel positif | upside illimité |

### Limite

La figure est un tableau de caractéristiques générales. Elle ne remplace pas le chiffrage par jambes,
strikes, maturités, coûts, liquidité, assignment et stress tests.

## Portfolio insurance — pages 268–272, figure 13-8

### Principe

Quand aucun put n'est disponible ou liquide, le hedger peut répliquer une option via rehedging du
sous-jacent. Le chapitre relie cela aux équivalences synthétiques :

- `long underlying + long put = long call`

Pour créer la protection d'un put, le hedger cherche donc à répliquer les caractéristiques d'un call
en ajustant dynamiquement la proportion de sous-jacent détenue.

### Hypothèses visibles

- exercise price : `100`
- time to expiration : `10 semaines`
- underlying price : `101.35`
- interest rate : `8 %`
- volatility : `18.3 %`

Le call théorique a un delta initial de `57`. Le hedger qui détient le sous-jacent doit donc vendre
`43 %` de l'actif pour répliquer une exposition équivalente à un long call.

### Figure 13-8 — réplication

| Semaine | Asset value | Delta du 100 call | % d'actif requis | Ajustement requis |
|---:|---:|---:|---:|---|
| 0 | 101.35 | 57 | 57 % | sell 43 % |
| 1 | 102.26 | 62 | 62 % | buy 5 % |
| 2 | 99.07 | 46 | 46 % | sell 16 % |
| 3 | 100.39 | 53 | 53 % | buy 7 % |
| 4 | 100.76 | 56 | 56 % | buy 3 % |
| 5 | 103.59 | 74 | 74 % | buy 18 % |
| 6 | 99.26 | 45 | 45 % | sell 29 % |
| 7 | 98.28 | 35 | 35 % | sell 10 % |
| 8 | 99.98 | 50 | 50 % | buy 15 % |
| 9 | 103.78 | 93 | 93 % | buy 43 % |
| 10 | 102.54 | 100 | 100 % | buy 7 % |

### Enseignement

La réplication force souvent à acheter quand le marché monte et vendre quand il baisse. Ce coût de
rehedging est assimilé au coût de la gamma de l'option. Si le marché est plus volatil que prévu, les
ajustements coûtent plus cher mais l'option aurait aussi eu une valeur théorique plus élevée. Si le
marché est moins volatil, les ajustements coûtent moins cher mais la valeur de l'option aurait été
plus faible.

### Limites pratiques

Le chapitre souligne :

- coûts de transaction élevés si on ajuste beaucoup de titres ;
- usage possible de futures sur indice pour réduire les coûts ;
- risque de base si l'indice ne réplique pas exactement le portefeuille ;
- absence de liquidité ou maturité inadéquate des options disponibles ;
- nécessité d'une estimation raisonnable de volatilité.

### Impact projet

Portfolio insurance est une forme de hedge dynamique. Pour Take Two, cela impose de simuler :

- trajectoires du sous-jacent ;
- delta cible par date ;
- coût de rebalancement ;
- coûts de transaction ;
- tracking error entre hedge et portefeuille réel ;
- risque de gap entre deux ajustements.

## Conclusions provisoires pour Take Two

1. Hedger avec options revient à choisir une assurance : coût certain ou risque résiduel.
2. Les protections achetées limitent le risque mais peuvent avoir un edge théorique négatif.
3. Les covered writes reçoivent une prime mais transforment souvent le profil en position short
   option synthétique.
4. Collars/fences rendent le coût visible mais échangent protection contre upside abandonné.
5. Le choix doit combiner objectif directionnel, niveau d'IV, budget de coût, risque maximal et
   liquidité.
6. Un hedge peut devenir un trade de volatilité si la structure crée un risque illimité ou un ratio
   excessif.
7. La protection doit être mesurée en delta, mais validée par scénarios et stress tests.
8. La réplication dynamique d'une option est possible théoriquement, mais dépend fortement des coûts,
   de la liquidité, des gaps et de l'estimation de volatilité.
9. Le futur script IBKR doit proposer une shortlist de hedges comparables, pas une recommandation
   unique automatique.
10. Chaque hedge doit afficher : risque éliminé, risque conservé, risque ajouté, coût net, edge
    théorique et sensibilité aux hypothèses.

## Prochaine source possible

Après Natenberg, les compléments les plus utiles sont :

- Passarelli — realized volatility, gamma scalping et P&L des hedges ;
- McMillan — variantes pratiques de stratégies options et sélection de structure ;
- Sinclair — règles plus quantitatives sur volatilité et sizing.
