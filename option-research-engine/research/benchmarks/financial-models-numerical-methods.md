# REPO-FMNM — Financial Models Numerical Methods (Cantaro86)

Nature : collection de notebooks de méthodes numériques. Licence : open source (voir repo).
Maturité : contenu stable, référence pédagogique. Étude ciblée : Black-Scholes, arbres binomiaux,
Monte Carlo, PDE, Heston, calcul stochastique, méthodes de Fourier, modèles numériques, pricing.
But : renforcer notre moteur de simulation.

## 1. Ce que ce projet fait mieux que nous
Implémentations de référence lisibles des modèles de pricing (BS, binomial, Heston, Fourier, PDE)
avec comparaisons numériques entre méthodes.

## 2. Ce qu'il ne fait pas
Pas de données réelles de chaînes d'options, pas de gestion de position, pas de calibration
industrialisée, pas de moteur de décision.

## 3. Ce que nous pouvons réutiliser
Les implémentations comme ORACLES de test : nos futurs composants de pricing/simulation devront
reproduire leurs résultats sur des cas canoniques (fichiers de cas à créer dans `benchmarks/`).
Le choix de méthode par contexte (vitesse/précision) alimentera des règles `MC`.

## 4. Ce que nous devons améliorer
Vectorisation/performance pour des milliers de trajectoires × candidats ; intégration du
repricing dans des chemins DÉPENDANTS (nos règles de maintenance simulées).

## 5. Pourquoi notre architecture sera différente
Ce repo démontre des méthodes ; notre simulateur les industrialise sous contrat de convergence
documenté (Glasserman) et au service exclusif du scoring de stratégies.
