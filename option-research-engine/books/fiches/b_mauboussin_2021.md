# B-MAUBOUSSIN-2021 — Expectations Investing

## Auteur
Michael J. Mauboussin & Alfred Rappaport

## Année
2021 (édition révisée)

## Catégorie
VALUATION (principale), DECISION

## Objectif
Donner au moteur une méthode pour lire les ATTENTES IMPLICITES dans le prix — l'entrée idéale
pour décider si un Call sur ce sous-jacent offre une asymétrie.

## Niveau de confiance
VALUATION : 5. Méthode explicite, reproductible, orientée décision.

## Pourquoi ce livre est important
Le module `valuation/` ne doit pas produire une « valeur intrinsèque » académique mais un signal
d'asymétrie : la méthode expectations (reverse-DCF + triggers de révision) est exactement cela.
Le livre traite même explicitement des options réelles et de leur lien avec les attentes.

## Modules concernés
sélection du sous-jacent, échéances (horizon des catalyseurs), scoring, simulation (scénarios).

## Informations recherchées (très précisément)
- Procédure complète de lecture des attentes implicites (étapes, données requises).
- Triggers de révision des attentes (ventes, marges, investissements) → variables surveillées.
- Construction des scénarios haut/bas et de la valeur espérée → alimentation directe des
  scénarios déterministes du simulateur.
- Signaux de surprises positives/négatives et de révisions de bénéfices.

## Prompt Gemini spécifique
Tu extrais des règles de « Expectations Investing ». Base : prompt VALUATION. Spécialisations :
(1) Convertis la méthode en une SÉQUENCE de règles chaînées (chaque étape = une règle, avec ses
Variables nécessaires listées pour le Module 3 données entreprise). (2) Chaque « trigger » de
révision devient une règle d'alerte pour le moteur de maintenance. (3) Relie explicitement chaque
règle produite au choix d'échéance : horizon du catalyseur → échéance minimale du Call. Sortie :
format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
