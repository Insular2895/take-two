# knowledge_base/ — Base de connaissances consolidée

## Rôle
Contenir l'état CONSOLIDÉ des connaissances : règles fusionnées, dédupliquées, pondérées — la
seule source que le futur moteur lira en production.

## Ce qui y sera stocké
- `index_regles.md` — index de toutes les règles `ACTIVE` par catégorie et par module.
- `registre_conflits.md` — tous les conflits (ouverts / tranchés) avec leur arbitrage.
- `matrice_convergences.md` — quelles règles sont soutenues par plusieurs livres (et lesquels).
- Fiches de règles consolidées quand une fusion crée une règle nouvelle (mêmes conventions que `rules/`).

## Format attendu
Markdown, format officiel des règles, index sous forme de tableaux (ID, titre, poids, statut, sources).

## Conventions
- Rien n'entre ici sans être passé par le pipeline complet (`docs/02` → `04`).
- Chaque nouveau livre ENRICHIT la base sans remplacer l'existant.
- Une règle consolidée référence TOUJOURS ses règles sources.

## Dépendances
`rules/` (amont), `docs/03` et `docs/04` (procédures), `decision_engine/` (consommateur).
