# B-GLASSERMAN-2003 — Monte Carlo Methods in Financial Engineering

## Auteur
Paul Glasserman

## Année
2003

## Catégorie
MC (principale), PROBA

## Objectif
Spécifier un simulateur Monte Carlo correct et efficace : discrétisation, réduction de variance,
quasi-MC, convergence — la colonne vertébrale de `monte_carlo/` et `simulations/`.

## Niveau de confiance
MC : 5. Référence académique absolue du domaine.

## Pourquoi ce livre est important
Toute la chaîne de décision repose sur des distributions simulées : une erreur de simulation
contamine scoring, sizing et classement. Ce livre fournit les règles de correction et d'efficacité.

## Modules concernés
simulation, robustesse, scoring (qualité des estimations).

## Informations recherchées (très précisément)
- Schémas de discrétisation et leurs biais → règles de choix de schéma par processus.
- Variance reduction (antithétiques, control variates, importance sampling) : conditions de gain.
- Quasi-Monte Carlo : quand il domine le MC standard.
- Estimation d'erreur et critères d'arrêt → règle de nombre de trajectoires par convergence.
- Simulation de processus à volatilité stochastique (pour Heston si adopté).

## Prompt Gemini spécifique
Tu extrais des règles de méthode depuis Glasserman. Base : prompt MC. Spécialisations : (1) Chaque
technique doit produire une règle coût/bénéfice : Condition = propriété du problème (payoff,
dimension, régularité), Action = technique recommandée, Risques = cas d'échec cités. (2) Les
théorèmes ne sont extraits QUE via leurs conséquences pratiques (vitesse de convergence →
critère d'arrêt). (3) Ignore les chapitres sans lien avec le pricing/simulation d'options sur
actions. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
