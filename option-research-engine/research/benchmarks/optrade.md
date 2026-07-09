# REPO-OPTRADE — OpTrade

Nature : repository orienté recherche et expérimentation sur les options.
Source GitHub repérée : <https://github.com/xmootoo/OpTrade>. Licence déclarée : MIT.
Langage principal : Python. Maturité : `to_audit`.
Étude ciblée : sélection automatique de contrats, moneyness,
expiration, volatilité, pipeline de données, expérimentation, modèles ML.

Statut d'intégration : `candidate_to_verify`.
Priorité : 5/5 — candidat à étudier quasiment au niveau de `gs-quant.md`.

## 1. Ce que ce projet fait mieux que nous
OpTrade semble couvrir directement le cœur de notre futur moteur : recherche sur options,
sélection de contrats, choix d'expiration, variables de moneyness et volatilité, pipeline de
données et expérimentation. C'est donc un benchmark plus proche de notre usage que les toolkits
financiers généralistes.

## 2. Ce qu'il ne fait pas
Il ne remplace pas notre corpus de règles sourcées, ni la validation 2026 des contraintes
opérationnelles : settlement, assignment, ex-dividend, marge, commissions, liquidité live,
stress de gap et validation humaine. Son statut exact, sa licence, ses dépendances, ses tests
et son niveau de maintenance doivent être audités dans le code avant toute réutilisation.

## 3. Ce que nous pouvons réutiliser
À étudier en priorité pour :

- la structure du pipeline de données options ;
- les features de sélection de contrats ;
- l'encodage moneyness / expiration / volatilité ;
- les patterns d'expérimentation et de scoring ML ;
- la séparation entre données, features, modèles et évaluation.

## 4. Ce que nous devons améliorer
Notre moteur doit rester plus strict sur les garde-fous : chaque recommandation devra relier la
thèse fondamentale, la structure optionnelle, les coûts exécutables, la liquidité, les Greeks,
la marge et les règles de sortie. OpTrade peut inspirer l'architecture de recherche, mais ne doit
pas court-circuiter le contrat de risque.

## 5. Pourquoi notre architecture sera différente
OpTrade est un candidat de recherche et d'expérimentation. Notre architecture vise un moteur de
décision explicable pour TTWO / GTA 6, avec règles normalisées, audit de fraîcheur 2026, données
IBKR live, validation humaine et journal post-trade. Toute inspiration venant d'OpTrade devra être
traduite en composants testables, non en dépendance implicite.
