# B-HULL-2021 — Options, Futures, and Other Derivatives

## Auteur
John C. Hull

## Année
2021 (11e édition)

## Catégorie
OPTIONS, MC, PROBA

## Objectif
Fournir les fondations théoriques exactes (pricing, Greeks, processus stochastiques,
Monte Carlo) sur lesquelles le simulateur et le repricing s'appuieront.

## Niveau de confiance
Théorie : 5. Référence académique mondiale. Peu de règles de trading directes (attendu).

## Pourquoi ce livre est important
Le moteur doit repricer des options le long de trajectoires simulées : Hull fournit les modèles
(Black-Scholes-Merton, binomial, volatilité stochastique) et leurs hypothèses/limites, à
documenter pour éviter les erreurs de simulation.

## Modules concernés
simulation, scoring, robustesse, valuation d'options.

## Informations recherchées (très précisément)
- Hypothèses et limites de Black-Scholes-Merton (à convertir en règles de validité du simulateur).
- Formules des Greeks et leurs comportements limites.
- Chapitres Monte Carlo : discrétisation, réduction de variance, pièges numériques.
- Traitement des dividendes et taux dans le pricing (règles de données requises).
- Smile/surface de volatilité : implications pour le repricing.

## Prompt Gemini spécifique
Tu extrais des règles de méthode depuis Hull. Base : prompts MC + PROBA. Spécialisations :
(1) Ce livre produit surtout des règles de type « validité » : « SI hypothèse H violée ALORS le
modèle M sous/surestime la valeur → utiliser M' ou corriger ». (2) Convertis chaque limite de
modèle explicitée par Hull en règle de robustesse pour le simulateur. (3) Extrait les formules
des Greeks en tant que Variables nécessaires normalisées pour tout le repository. (4) Ignore les
chapitres sur swaps, crédit et taux exotiques. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
