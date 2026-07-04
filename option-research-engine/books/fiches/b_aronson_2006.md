# B-ARONSON-2006 — Evidence-Based Technical Analysis

## Auteur
David Aronson

## Année
2006

## Catégorie
PROBA / Backtesting (principale), ALGO

## Objectif
Immuniser le moteur contre l'overfitting et le data mining : tests statistiques corrects,
biais de sélection, significativité des backtests.

## Niveau de confiance
Backtesting/PROBA : 5 pour la méthodologie.

## Pourquoi ce livre est important
Le moteur teste automatiquement des milliers de combinaisons (Module 5) : sans les corrections de
data mining d'Aronson, le classement récompensera mécaniquement le hasard.

## Modules concernés
validation, backtesting, robustesse, scoring (pénalisation de la sur-optimisation).

## Informations recherchées (très précisément)
- Biais de data mining : quantification et méthodes de correction (White's Reality Check, etc.).
- Protocoles de test hors échantillon et leurs pièges.
- Critères de significativité adaptés aux tests multiples → règles de seuil du moteur.
- Erreurs de logique d'inférence listées par l'auteur → règles d'interdiction méthodologiques.

## Prompt Gemini spécifique
Tu extrais des règles de méthode depuis Aronson. Base : prompt PROBA/ALGO. Spécialisations :
(1) Chaque biais décrit produit une règle de protection du pipeline de validation (Condition =
situation de test, Action = correction obligatoire). (2) Convertis les corrections de tests
multiples en règles chiffrées applicables au Module 5 (nombre de stratégies testées → seuil de
significativité ajusté). (3) Ignore les chapitres d'inventaire d'indicateurs techniques. Sortie :
format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
