# B-TALEB-1997 — Dynamic Hedging

## Auteur
Nassim Nicholas Taleb

## Année
1997

## Catégorie
GREEKS, RISK, VOL

## Objectif
Documenter les comportements des Greeks dans les cas extrêmes et les risques de second ordre
(gamma des ailes, comportement près de l'échéance, liquidité) pour renforcer robustesse et garde-fous.

## Niveau de confiance
GREEKS/RISK : 4. Très riche mais dense ; règles à reformuler soigneusement en conditions testables.

## Pourquoi ce livre est important
La plupart des livres décrivent les Greeks en régime calme. Taleb décrit leurs pathologies —
exactement ce que les stress tests et les règles d'exception doivent couvrir.

## Modules concernés
robustesse, risque, alertes, maintenance, simulation (scénarios extrêmes).

## Informations recherchées (très précisément)
- Comportements des Greeks près de l'échéance et près du strike (pin risk, explosion du Gamma).
- Risques de liquidité et d'exécution sur options (spreads en stress).
- Volatilité : skew, comportement en crise, implications pour un détenteur de Calls.
- Situations où les mesures standards (Delta, Vega) deviennent trompeuses → règles d'exception.

## Prompt Gemini spécifique
Tu extrais des règles de « Dynamic Hedging » (Taleb). Base : prompts GREEKS + RISK.
Spécialisations : (1) Cible les descriptions de régimes EXTRÊMES : chaque pathologie décrite
devient une règle d'exception ou d'alerte (Condition = régime détectable, Action = alerter /
interdire / élargir les stress tests). (2) Le vocabulaire de Taleb est idiosyncratique : normalise
vers le vocabulaire du repository (CONVENTIONS.md). (3) Ignore les sections purement dédiées aux
books de market makers exotiques, sauf si la règle protège un acheteur de Calls. Sortie : format
officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
