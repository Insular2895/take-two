# B-PASSARELLI-2012 — Trading Options Greeks

## Auteur
Dan Passarelli

## Année
2012 (2e édition)

## Catégorie
GREEKS (principale), OPTIONS

## Objectif
Transformer les Greeks en décisions automatiques : seuils critiques, dominance d'un Greek selon
le contexte, critères de vente et de rolling pilotés par les Greeks.

## Niveau de confiance
GREEKS : 4. Praticien pédagogue ; règles concrètes, exemples chiffrés abondants.

## Pourquoi ce livre est important
C'est le livre le plus directement exploitable pour le module `greeks/` : il relie chaque Greek à
une décision de gestion, avec des exemples numériques complets.

## Modules concernés
sélection, maintenance, vente, rolling, alertes, surveillance des Greeks.

## Informations recherchées (très précisément)
- Seuils de Delta pour le choix de moneyness selon l'objectif (directionnel vs levier).
- Interaction Gamma/Theta selon jours restants → règles de fenêtre de détention.
- Vega et positionnement avant/après événements → règles de timing.
- Signaux de vente/rolling fondés sur l'évolution des Greeks de la position.
- Erreurs de lecture des Greeks explicitement décrites.

## Prompt Gemini spécifique
Tu extrais des règles de « Trading Options Greeks » (Passarelli). Base : prompt GREEKS.
Spécialisations : (1) Chaque exemple numérique du livre doit produire une règle générale + son
exemple chiffré dans le champ Exemple. (2) Quand l'auteur décrit un « trade-off » (ex. Gamma vs
Theta), produis une règle de bascule avec la variable de bascule explicite (jours restants,
distance au strike). (3) Les chapitres sur la volatilité implicite doivent produire des règles
croisées Vega×IV Rank. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- 2026-07-05 — OCR intégral et recherche ciblée terminés — 31 blocs, 20 candidates avec preuve
  vérifiée, 14 formulations `to_review`; aucune règle activée.
