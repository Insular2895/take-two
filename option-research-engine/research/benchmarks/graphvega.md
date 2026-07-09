# REPO-GRAPHVEGA — GraphVega

Nature : repository candidat pour visualisation d'options et de sensibilités.
Source GitHub repérée : <https://github.com/rahuljoshi44/GraphVega>. Licence déclarée : MIT.
Langage principal : JavaScript. Maturité : `to_audit` ; attention, activité de code à vérifier
avant tout usage. Étude ciblée : courbes P/L, Greeks, scénarios, visualisation pédagogique et
future interface utilisateur.

Statut d'intégration : `candidate_to_verify`.
Priorité : 4/5 — utile pour l'UI et l'analyse visuelle, pas pour le moteur de décision.

## 1. Ce que ce projet fait mieux que nous
GraphVega est surtout intéressant pour rendre lisibles les structures : profils de payoff,
courbes P/L, visualisation des Greeks et scénarios. Ce type d'outil peut accélérer la future UI,
notamment pour comparer action seule, call/put, vertical spread, calendar, butterfly, straddle,
strangle ou hedge.

## 2. Ce qu'il ne fait pas
Il ne doit pas être traité comme une source de vérité mathématique ou opérationnelle. Une
visualisation ne valide ni le pricing, ni la liquidité, ni l'assignment, ni la marge, ni
l'exécutabilité du bid/ask. Sa licence, ses dépendances, son activité de maintenance et ses
conventions d'unités doivent être vérifiées avant usage.

## 3. Ce que nous pouvons réutiliser
À étudier pour :

- les composants de visualisation P/L ;
- la représentation des Greeks par scénario ;
- les vues avant/après variation du sous-jacent, de la volatilité, du temps et des taux ;
- les patterns UI utiles pour expliquer une décision au lieu d'afficher seulement un score.

## 4. Ce que nous devons améliorer
Notre UI devra afficher les limites autant que les opportunités : bid/ask exécutable, slippage,
pin risk, assignment, ex-dividend, coûts, marge, stress de gap et règles de sortie. Une jolie
courbe P/L sans ces alertes serait dangereuse pour un outil de décision.

## 5. Pourquoi notre architecture sera différente
GraphVega peut devenir une inspiration visuelle. Le moteur restera séparé : calcul, validation,
scoring, données live et garde-fous ne doivent pas dépendre d'une librairie d'affichage. La future
UI consommera des résultats audités par le moteur, pas l'inverse.
