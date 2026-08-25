# Registre des sources — version de lecture française

Date : 2026-08-08  
Registre canonique : [`source_registry.yaml`](source_registry.yaml)  
Nombre de sources canoniques : 36

## Comment lire ce document

Cette page explique le rôle des sources en français. Elle ne remplace pas le YAML canonique, qui
contient les chemins, pages, hypothèses, mesures, limites, symboles de code et états exacts.
`Sourcé` signifie qu’une source pertinente a été inspectée ; cela ne signifie pas qu’un modèle a
été validé sur des données TTWO réelles.

## Livres et fragments locaux

| Identifiant | Source | Utilisation dans le dépôt | État |
| --- | --- | --- | --- |
| `book-bergomi-stochastic-volatility-modeling` | Lorenzo Bergomi, *Stochastic Volatility Modeling*, chap. 3–12 et épilogue | Heston, variance forward, sourire, volatilité locale-stochastique ; surtout utilisé pour définir les portes avant modèles avancés | sourcé, corpus incomplet |
| `book-andersen-piterbarg-interest-rate-modeling` | Andersen & Piterbarg, *Interest Rate Modeling*, volumes I–II partiels | mesures `P/Q`, actualisation, méthodes numériques, Monte Carlo, courbes et modèles de taux | sourcé |
| `book-glasserman-monte-carlo` | Paul Glasserman, *Monte Carlo Methods in Financial Engineering* | erreur standard, intervalle Monte Carlo, variable de contrôle, antithétiques, arrêt optimal | testé |
| `book-suli-mayers-numerical-analysis` | Süli & Mayers, *An Introduction to Numerical Analysis* | bissection, conditionnement, erreur absolue/relative, raffinement de grille | sourcé |
| `book-nocedal-wright-numerical-optimization` | Nocedal & Wright, *Numerical Optimization* | référence secondaire ; aucune méthode locale continue ne remplace l’oracle entier | proposé |
| `book-boyd-vandenberghe-convex-optimization` | Boyd & Vandenberghe, *Convex Optimization* | dominance, optimalité de Pareto et limites de la scalarisation | testé |
| `book-tsay-analysis-financial-time-series` | Ruey Tsay, *Analysis of Financial Time Series* | EWMA, GARCH(1,1), résidus et prévisions chronologiques | sourcé |
| `book-mcelreath-statistical-rethinking` | Richard McElreath, *Statistical Rethinking* | sens du posterior, prédiction, mélange de modèles et risque de surconfiance | testé |
| `book-blitzstein-hwang-introduction-probability` | Blitzstein & Hwang, *Introduction to Probability* | probabilité conditionnelle, indépendance, mélange de scénarios et seuil de croyance | testé |
| `book-wasserman-all-statistics` | Larry Wasserman, *All of Statistics* | bootstrap, tests de permutation et limites des petits échantillons | testé |
| `book-bjork-arbitrage-theory` | Tomas Björk, *Arbitrage Theory in Continuous Time* | frontière `P/Q`, valorisation risque-neutre et Black–Scholes | sourcé |
| `book-sarkka-svensson-bayesian-filtering-smoothing` | Särkkä & Svensson, *Bayesian Filtering and Smoothing* | exigences d’un modèle d’état ; filtre différé faute de transition/observation identifiées | sourcé |

## Livres demandés mais absents

| Identifiant | Source manquante | Conséquence |
| --- | --- | --- |
| `book-gatheral-volatility-surface` | Jim Gatheral, *The Volatility Surface* | le livre local manque ; les articles primaires SVI/SSVI inspectés servent pour les formules utilisées |
| `book-shreve-stochastic-calculus-finance-ii` | Steven Shreve, volume II | ne pas substituer silencieusement le volume I ; Björk et Andersen–Piterbarg couvrent les contrats actuellement retenus |

## Articles méthodologiques

| Identifiant | Sujet retenu | État/limite principale |
| --- | --- | --- |
| `paper-kunsch-block-bootstrap` | bootstrap par blocs pour observations stationnaires dépendantes | testé ; choix de longueur toujours sensible |
| `paper-clement-lamberton-protter-lsm` | analyse de Longstaff–Schwartz | sourcé ; implémentation différée |
| `paper-brier-probability-forecast-verification` | score de Brier pour prévisions probabilistes | testé sur cas synthétiques |
| `paper-wilson-binomial-interval` | intervalle binomial de Wilson | testé ; réservé aux essais Bernoulli non pondérés compatibles |
| `paper-gatheral-jacquier-svi` | SVI sans arbitrage | sourcé et implémenté sur diagnostics synthétiques |
| `paper-cohort-corbetta-martini-laachir-ssvi` | calibration robuste de tranches SSVI | sourcé ; pas de promotion empirique |
| `paper-mingone-essvi` | paramétrisation globale eSSVI | sourcé ; modèle non intégré |
| `paper-bailey-borwein-lopez-zhu-pbo` | probabilité de surapprentissage de backtest | métadonnées primaires inspectées ; conformité texte intégral à revoir |
| `paper-bailey-lopez-deflated-sharpe` | ratio de Sharpe déflaté | implémentation explicitement approximative |
| `paper-gatheral-jaisson-rosenbaum-volatility-rough` | rugosité de la volatilité | source primaire ; données surtout larges fréquences, non TTWO |
| `paper-bayer-friz-gatheral-pricing-rough-volatility` | tarification rough Bergomi | preuve SPX, pas de gain TTWO démontré |
| `paper-livieri-mouti-pallavicini-rosenbaum-option-roughness` | rugosité observée dans les prix d’options | source SPX court terme ; non transférée automatiquement à TTWO |

## Sources officielles, données et documentation logicielle

| Identifiant | Rôle | Limite |
| --- | --- | --- |
| `repo-readme-v11-1` | contrat et fonctionnement historique du dépôt | preuve interne, pas validation financière |
| `official-quantlib-1-43` | référence de comparaison pour les prix européens et différences finies | cohérence numérique seulement |
| `official-alpaca-historical-options-2026` | faisabilité des données historiques d’options | disponibilité/licence à confirmer pour une campagne réelle |
| `official-marketdata-option-chain-2026` | chaîne d’options et champs disponibles | provenance et point-in-time à gouverner |
| `official-ibkr-market-data-2026` | abonnements et contraintes de données IBKR | aucun ordre ni flux live activé |
| `official-occ-odd-2024-current-page-2026` | terminologie et risques officiels des options standardisées | document de risque, pas preuve quantitative |
| `official-fred-alfred-realtime-periods-2026` | vintages et périodes de disponibilité des données macro | sert à empêcher le look-ahead |
| `official-us-treasury-daily-rates-2026` | courbe de taux quotidienne officielle | base déterministe ; modèle de taux stochastique non justifié |

## Preuves internes

| Identifiant | Rôle | Portée |
| --- | --- | --- |
| `internal-phase10-validation-evidence` | audit intégral, statuts de release et blocages | confirme le niveau logiciel, pas la performance de marché |
| `internal-phase11-extension-evaluation` | classement des onze extensions avancées | portes réversibles ; aucun modèle avancé intégré |

## Limites communes

- Une page ou formule n’est retenue qu’avec une provenance enregistrée.
- Les PDF sont restés en lecture seule ; 61 fichiers demandent une prudence structurelle accrue.
- Un résumé n’est jamais une preuve quantitative autonome.
- Les sources sur indices ou SPX ne démontrent pas une validité pour TTWO.
- Le registre peut prouver l’identité et la traçabilité d’une source, pas la qualité d’un futur jeu
  de données réel.

