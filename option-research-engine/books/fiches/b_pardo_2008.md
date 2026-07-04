# B-PARDO-2008 — The Evaluation and Optimization of Trading Strategies

## Auteur
Robert Pardo

## Année
2008 (2e édition)

## Catégorie
TRADSYS / Backtesting (principale)

## Objectif
Fournir le protocole Walk-Forward complet : optimisation correcte des paramètres (stops,
trailing, sorties) sans overfitting, et mesure de robustesse.

## Niveau de confiance
Backtesting : 5. L'ouvrage de référence du Walk-Forward Analysis.

## Pourquoi ce livre est important
Nos paramètres de maintenance (trailing stops, récupération du capital, rolling) ne doivent
jamais être codés en dur : ils sortent d'une optimisation. Pardo définit COMMENT optimiser sans
se mentir — c'est le protocole officiel de `validation/`.

## Modules concernés
validation, backtesting, maintenance (calibration des paramètres), robustesse.

## Informations recherchées (très précisément)
- Protocole Walk-Forward : tailles de fenêtres, ré-optimisation, Walk-Forward Efficiency → règles chiffrées.
- Critères de robustesse d'un paramètre (plateaux vs pics) → règles de sélection de paramètres.
- Signes d'overfitting listés par l'auteur → règles de rejet automatique d'une stratégie.
- Mesures d'évaluation d'un système au-delà du profit total.

## Prompt Gemini spécifique
Tu extrais des règles depuis Pardo. Base : prompts TRADSYS + PROBA. Spécialisations : (1) Le
protocole Walk-Forward doit sortir en règles chaînées numérotées, exécutables comme une checklist
par le pipeline de validation. (2) Chaque heuristique de robustesse (ex. préférer un plateau de
paramètres) devient une règle avec sa mesure exacte. (3) Adapte le vocabulaire « système sur
futures » vers notre contexte options quand la logique est transposable ; note la transposition
dans Risques. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
