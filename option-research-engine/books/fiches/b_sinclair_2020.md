# B-SINCLAIR-2020 — Positional Option Trading

## Auteur
Euan Sinclair

## Année
2020

## Catégorie
OPTIONS, PROBA, MM

## Objectif
Fournir des règles d'edge mesurable pour positions d'options tenues plusieurs jours/semaines :
quand un acheteur de Calls a réellement un avantage, et comment le dimensionner.

## Niveau de confiance
OPTIONS/PROBA : 4–5. Approche sceptique et quantifiée, idéale contre les règles arbitraires.

## Pourquoi ce livre est important
Sinclair y documente OÙ se trouvent les edges (variance premium, skew, événements) et surtout où
ils N'EXISTENT PAS — indispensable pour empêcher le moteur d'optimiser du bruit.

## Modules concernés
sélection, sizing, scoring, robustesse, garde-fous.

## Informations recherchées (très précisément)
- Inventaire des edges documentés avec leur amplitude et leurs conditions de persistance.
- Règles de sizing sous incertitude de l'edge (Kelly fractionné).
- Critères de choix de structure (Call sec vs spread) selon l'edge visé.
- Résultats négatifs : stratégies dont l'auteur démontre l'absence d'edge (→ règles d'interdiction).

## Prompt Gemini spécifique
Tu extrais des règles de « Positional Option Trading » (Sinclair 2020). Base : prompts OPTIONS +
PROBA. Spécialisations : (1) Chaque edge documenté devient une règle avec l'amplitude chiffrée
citée par l'auteur et ses conditions de validité. (2) Chaque démonstration d'ABSENCE d'edge
devient une règle d'interdiction (Action = « ne pas fonder une décision sur X »), c'est aussi
précieux qu'une règle positive. (3) Les recommandations de sizing doivent citer la fraction de
Kelly exacte proposée. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
