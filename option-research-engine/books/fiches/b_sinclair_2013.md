# B-SINCLAIR-2013 — Volatility Trading

## Auteur
Euan Sinclair

## Année
2013 (2e édition)

## Catégorie
VOL (principale), PROBA, MM

## Objectif
Doter le moteur de mesures de volatilité rigoureuses (HV, cônes, IV) et de règles d'entrée/sortie
fondées sur l'écart IV vs volatilité réalisée prévisible.

## Niveau de confiance
VOL : 5 — MM : 4 (chapitre Kelly). Quant reconnu, approche empirique et testable.

## Pourquoi ce livre est important
C'est le livre le plus opérationnel sur la MESURE de la volatilité : estimateurs
(close-to-close, Parkinson, Garman-Klass, Yang-Zhang), cônes de volatilité, prévision — exactement
ce que le module `volatility/` doit spécifier.

## Modules concernés
sélection, simulation, scoring, sizing, entrée/sortie liées à la volatilité.

## Informations recherchées (très précisément)
- Chaque estimateur de HV : formule, biais, conditions d'usage → règles de choix d'estimateur.
- Construction et lecture des cônes de volatilité → règles d'entrée (IV vs cône).
- Prévisibilité de la volatilité (clustering, mean reversion) → règles de timing.
- Chapitre sur le Kelly criterion appliqué au trading de volatilité → règles de sizing.
- Comportement de l'IV autour des earnings → règles pré/post événement.

## Prompt Gemini spécifique
Tu extrais des règles de « Volatility Trading » (Sinclair). Base : prompt VOL. Spécialisations :
(1) Pour chaque estimateur de volatilité, produis DEUX règles : une règle de calcul (variables,
fenêtre, données requises) et une règle de choix (quand préférer cet estimateur). (2) Convertis
chaque résultat empirique chiffré (tableaux) en seuil avec son intervalle de validité. (3) Le
chapitre sur le money management doit produire des règles Kelly avec la fraction recommandée par
l'auteur et ses conditions. (4) Ignore les sections spécifiques à la vente de volatilité SAUF
si elles définissent l'IV Crush utile à l'acheteur. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
