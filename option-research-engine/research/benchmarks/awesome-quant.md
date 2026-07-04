# REPO-AWESOME-QUANT — Awesome Quant

Nature : liste curée (pas un logiciel). Licence : CC/MIT selon entrées. Maturité : très active.
Objectif pour nous : cartographie complète du domaine — bibliothèques Python, moteurs de pricing,
Monte Carlo, Greeks, Black-Scholes/Heston/SABR, optimisation, portefeuille, risk management,
backtesting, ML, data providers, calendriers de marché, visualisation, papers, livres, outils pro.

## 1. Ce que ce projet fait mieux que nous
Exhaustivité de la veille : il recense l'état de l'art plus vite que nous ne pourrons jamais le faire.

## 2. Ce qu'il ne fait pas
Aucune évaluation qualitative sérieuse, aucune cohérence d'ensemble, aucun moteur de décision,
aucune traçabilité scientifique des règles. C'est un annuaire, pas une base de connaissances.

## 3. Ce que nous pouvons réutiliser
La cartographie elle-même : chaque brique candidate (pricing, MC, Greeks, calendriers, data)
identifiée ici reçoit une fiche `templates/fiche_repository.md` avant toute considération d'usage.

## 4. Ce que nous devons améliorer
Filtrer par maturité/licence/maintenance ; évaluer chaque brique contre NOS besoins (repricing le
long de trajectoires, chemins dépendants pour trailing stops simulés) plutôt que par popularité.

## 5. Pourquoi notre architecture sera différente
Notre système est piloté par des règles sourcées et validées, pas par un assemblage de librairies.
Les briques externes sont des fournisseurs de calcul interchangeables derrière nos interfaces.
