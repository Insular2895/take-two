# REPO-ML4T — Machine Learning for Trading (Stefan Jansen)

Nature : livre + notebooks compagnons. Licence : code open source (voir repo). Maturité : élevée,
très utilisé. Étude ciblée : architecture des notebooks, workflow de recherche, validation
statistique, construction des features, backtesting, optimisation, gestion des données, pipeline
de recherche. But : améliorer notre méthodologie scientifique.

## 1. Ce que ce projet fait mieux que nous
Pédagogie du pipeline de recherche complet : de la donnée brute à l'évaluation, avec les pièges
de validation propres aux séries financières traités explicitement.

## 2. Ce qu'il ne fait pas
Presque rien d'opérationnel sur les options ; pas de moteur de règles ; les notebooks sont des
démonstrations, pas un système de production.

## 3. Ce que nous pouvons réutiliser
Les protocoles de validation (splits temporels corrects, prévention du lookahead), l'organisation
donnée→feature→test, et sa bibliographie comme source d'entrées pour `references/`.

## 4. Ce que nous devons améliorer
Passer de notebooks exploratoires à des protocoles NORMÉS (nos règles de `validation/` doivent
être des checklists exécutables, pas des exemples).

## 5. Pourquoi notre architecture sera différente
Le ML y est le produit ; chez nous il est au mieux un composant, admis uniquement s'il bat les
règles issues de la littérature dans nos benchmarks (`benchmarks/`).
