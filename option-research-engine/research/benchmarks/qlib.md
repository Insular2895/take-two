# REPO-QLIB — Microsoft Qlib

Nature : plateforme de recherche quantitative orientée ML. Licence : MIT. Maturité : élevée,
maintenue par Microsoft. Étude ciblée : pipeline de données, système de recherche, scoring,
moteurs ML, backtesting, validation, workflow, séparation des modules, gestion des datasets,
architecture des agents. But : comprendre les meilleures pratiques de Microsoft, pas copier Qlib.

## 1. Ce que ce projet fait mieux que nous
Industrialisation de la recherche : pipeline données→features→modèle→backtest reproductible,
gestion des expériences (versioning, comparaison), séparation nette des couches.

## 2. Ce qu'il ne fait pas
Rien sur les options : pas de Greeks, pas d'IV, pas de structures multi-jambes, pas de moteur de
règles issues de littérature, pas d'explicabilité par sources.

## 3. Ce que nous pouvons réutiliser
Les PATTERNS d'architecture : abstraction dataset/handler, workflow déclaratif des expériences,
enregistrement systématique des runs (transposable à notre journal de décision et à `validation/`).

## 4. Ce que nous devons améliorer
Adapter le backtesting « portefeuille d'actions » à des positions d'options avec maintenance
(chemins dépendants) ; remplacer le scoring ML opaque par notre scoring décomposable et sourcé.

## 5. Pourquoi notre architecture sera différente
Qlib optimise des prédictions ; nous optimisons des DÉCISIONS contraintes par des règles
documentées. Le cœur de notre moteur est la base de connaissances, pas le modèle.
