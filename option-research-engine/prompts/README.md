# prompts/ — Prompts Gemini

## Rôle
Centraliser les prompts d'extraction. Deux niveaux :
1. **Prompts de catégorie** (`categories/`) — un par catégorie officielle. Ils définissent QUOI
   chercher dans un domaine.
2. **Prompts de livre** — dans chaque fiche de `books/fiches/`. Ils spécialisent le prompt de
   catégorie pour un livre précis (chapitres cibles, vocabulaire de l'auteur). **Aucun livre n'est
   traité avec un prompt générique.**

## Format attendu
Modèle : `templates/prompt_categorie.md`. Chaque prompt impose le format de sortie unique
(règle complète, jamais de résumé).

## Sélection automatique
Avant chaque lecture, le pipeline : identifie le type de livre → identifie son domaine
d'expertise → sélectionne le prompt de catégorie le plus adapté → applique la spécialisation de
la fiche livre.

## Conventions
Les prompts sont versionnés (v1, v2…) ; la version utilisée est notée dans le journal de
traitement de la fiche livre.
