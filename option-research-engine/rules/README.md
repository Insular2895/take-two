# rules/ — Règles atomiques extraites

## Rôle
Stocker chaque règle extraite de la littérature, une règle par fichier, au format officiel unique.

## Structure
```
rules/
├── FORMAT_REGLE.md        ← format officiel obligatoire
├── OPTIONS/  GREEKS/  VOL/  TRADSYS/  PSY/  MM/  RISK/  PROBA/
├── MC/  VALUATION/  ALGO/  ML/  DECISION/  BEHAV/
```
Les sous-dossiers de catégories sont créés au premier dépôt de règle.

## Format attendu
- Un fichier = une règle = `R-<CAT>-<NNN>.md` (ex. `R-VOL-003.md`).
- Contenu conforme à `FORMAT_REGLE.md`, tous champs obligatoires remplis.

## Conventions
- Statuts canoniques (champ `Statut`) : `DRAFT`, `EXTRACTED`, `VALIDATED`, `CONTRADICTED`, `DEPRECATED`.
- Les anciens libellés (`EXTRAITE`, `NORMALISÉE`, etc.) peuvent rester dans l'`Historique` pour
  expliquer l'ancien pipeline, mais ils ne pilotent pas l'activation du moteur.
- Une règle n'est jamais supprimée : elle change de statut ou elle est remplacée par une règle reliée.

## Dépendances
`docs/02_pipeline_extraction.md` (production), `docs/03_contradictions_et_doublons.md` (consolidation),
`knowledge_base/` (consommation).

## Revue de validité 2026

Index central : `../research/documentary/RULES_2026_REVIEW_INDEX.md`.

Les règles présentes ici peuvent être valides comme principes, mais ne deviennent jamais actives sans
données live, sources actuelles, contrôles broker et validation humaine explicite.
