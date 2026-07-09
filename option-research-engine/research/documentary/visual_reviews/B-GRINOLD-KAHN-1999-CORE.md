# Revue documentaire ciblée — B-GRINOLD-KAHN-1999

Source : Richard C. Grinold et Ronald N. Kahn, *Active Portfolio Management*, 2e édition.

Statut : `to_review`

Date de revue : 2026-07-06.

Périmètre : risque, information ratio, loi fondamentale, contraintes, turnover et coûts.

Les équations clés ont été contrôlées sur des rendus locaux du PDF. Les blocs marqués
`needs_review` par Transcript n'étaient pas illisibles : la plupart échouaient parce que la courte
citation textuelle ne contenait pas l'équation complète.

## Risque et annualisation — chapitre 3

Sous l'hypothèse de rendements non autocorrélés :

- la variance croît proportionnellement au temps ;
- l'écart-type croît avec la racine carrée du temps ;
- `σ_annuel = σ_mensuel × √12`.

L'hypothèse d'indépendance temporelle doit être testée. Une annualisation mécanique est trompeuse
si les rendements présentent autocorrélation, changements de régime ou données irrégulières.

Le risque actif est défini à partir de l'écart de rendement au benchmark. Le coût du risque dans la
fonction d'utilité est quadratique :

`coût du risque actif = λ_A × ψ_P²`

où `λ_A` représente l'aversion au risque actif et `ψ_P` le risque actif.

## Modèles de covariance — chapitre 3

Une covariance historique estimée sur `T` périodes pour `N` actifs devient singulière lorsque
`T ≤ N`. Les auteurs avertissent qu'elle peut alors faire apparaître comme sans risque certaines
positions actives.

Conséquence projet :

- refuser une covariance non conditionnée ;
- exposer le nombre d'observations, le rang et le conditionnement ;
- préférer une structure factorielle ou une régularisation validée lorsque la dimension est élevée ;
- ne jamais assimiler une variance numérique proche de zéro à l'absence économique de risque.

Le modèle factoriel décompose la covariance en :

`V = X F Xᵀ + Δ`

avec expositions `X`, covariance factorielle `F` et risque spécifique `Δ`. L'hypothèse de
covariances spécifiques nulles hors diagonale reste une hypothèse à tester.

## Information ratio et agressivité — chapitre 5

Sur la frontière résiduelle :

`VA(ω) = ω × IR − λ_R × ω²`

Le risque résiduel optimal est :

`ω* = IR / (2 × λ_R)`

La valeur ajoutée optimale devient :

`VA* = IR² / (4 × λ_R) = (ω* × IR) / 2`

Ces équations sont une fonction d'utilité, pas une garantie de rendement. Le paramètre `λ_R` est un
choix de gouvernance et le `IR` estimé possède une forte incertitude.

L'information ratio change avec l'horizon sous les mêmes hypothèses de scaling racine du temps.
Ainsi, un IR trimestriel vaut approximativement la moitié d'un IR annuel.

## Loi fondamentale — chapitre 6

Formule contrôlée :

`IR ≈ IC × √BR`

- `IC` : corrélation entre prévisions et résultats ;
- `BR` : nombre annuel de paris réellement indépendants.

Les auteurs présentent cette relation comme une approximation donnant de l'intuition, pas comme un
outil opérationnel direct. Le principal danger est de compter des signaux corrélés comme des paris
indépendants. Les contraintes de vente à découvert et d'implémentation réduisent aussi le résultat
réalisable.

Exemple documentaire important : après prise en compte d'un turnover annuel de `100 %` et de coûts
aller-retour de `0,80 %`, l'information ratio d'un exemple baisse sensiblement. Le skill brut et la
breadth ne suffisent donc pas.

## Coûts et turnover — chapitres 14 à 16

Le coût complet d'implémentation comprend au minimum :

- commissions ;
- bid-ask ;
- impact de marché ;
- coût d'opportunité des ordres non exécutés ;
- coût du délai ;
- turnover nécessaire au maintien du portefeuille.

L'`implementation shortfall` compare le portefeuille effectivement obtenu à un portefeuille papier
de référence. Ignorer les ordres non exécutés sous-estime le coût réel.

La relation valeur ajoutée / turnover est croissante mais concave : chaque unité supplémentaire de
turnover apporte généralement moins de valeur marginale. Le niveau optimal se situe lorsque valeur
marginale et coût marginal de transaction se rencontrent.

La règle documentaire « au moins 75 % de la valeur ajoutée incrémentale avec 50 % du turnover »
constitue une borne issue du modèle des auteurs. Elle ne doit pas devenir un seuil de production
sans reproduction mathématique et test empirique.

## Impact projet

Le moteur devra :

- distinguer signal brut, IC estimé, breadth effective et IR net ;
- réduire la breadth pour les signaux corrélés ;
- propager l'incertitude des estimations au sizing ;
- contrôler rang, conditionnement et stabilité de la covariance ;
- calculer un score après contraintes, turnover et coûts ;
- mesurer l'implementation shortfall et les ordres non exécutés ;
- empêcher qu'une formule de fonction d'utilité devienne une recommandation sans validation.
