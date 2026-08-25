# Risque de modèle

Les sorties V11.1 sont des outils de recherche. Les probabilités manuelles, paramètres
synthétiques, likelihoods non calibrées et surfaces fallback empêchent toute
qualification financière validée.

## Risques suivis

- erreur de spécification et changement de régime ;
- calibration instable ou non identifiable ;
- violation de la condition de Feller ;
- arbitrage calendaire, butterfly ou monotonicité de surface ;
- erreur Monte-Carlo et non-convergence ;
- désaccord GBM/local-vol/Heston/Heston+jumps ;
- dépendance aux priors et likelihoods ;
- confusion entre croyance heuristique configurée et posterior statistique calibré ;
- poids d'ensemble égaux/utilisateur pris à tort pour des probabilités de modèle ;
- biais de sélection, surapprentissage et contamination du holdout ;
- coûts, liquidité, FX, gap et quote combo indisponible.

Chaque métrique de simulation porte seed, nombre de trajectoires, pas, erreur standard,
intervalle à 95 %, statut de convergence, validité et statut de calibration. Le score
de robustesse ne contourne aucun veto : modèle invalide, données insuffisantes ou
stress bloquant restent visibles.

## Interprétation

Un bon rang expérimental n’est ni un ordre, ni une recommandation, ni une promesse.
Lorsque les modèles divergent, le verdict devient `model_dependent`, `fragile` ou
`data_insufficient`. `NO_TRADE` et le cash sont des résultats normaux.

Le champ legacy `BayesianScenarioDistribution` décrit actuellement une croyance heuristique
configurée. L'interface et les rapports l'étiquettent comme telle. Une revendication statistique
exigerait un outcome observé, une likelihood générative, des priors contrôlés, des vérifications
prior/posterior predictive et une validation OOS hachée.
