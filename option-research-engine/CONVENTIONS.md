# Conventions du repository

## Langue et format

- Langue de travail : **français** (les citations de livres restent dans leur langue d'origine).
- Format unique : **Markdown** (`.md`), UTF-8, une phrase par idée, pas de HTML.
- Les nombres utilisent le point décimal (`0.30`), les pourcentages sont explicites (`30 %`).

## Nommage

- Fichiers : `snake_case`, minuscules, sans accents : `option_volatility_and_pricing.md`.
- Fichiers ordonnés : préfixe numérique à deux chiffres : `01_selection_strategie.md`.
- Règles : identifiant unique `R-<CATEGORIE>-<NNN>` (ex. `R-GREEKS-014`, `R-VOL-003`).
- Livres : identifiant `B-<AUTEUR>-<ANNEE>` (ex. `B-NATENBERG-1994`).
- Repositories : identifiant `REPO-<NOM>` (ex. `REPO-QLIB`).

## Catégories officielles

`OPTIONS`, `GREEKS`, `VOL`, `TRADSYS`, `PSY`, `MM` (money management), `RISK`, `PROBA`,
`MC` (Monte Carlo), `VALUATION`, `ALGO`, `ML`, `DECISION`, `BEHAV`.

## Niveaux de confiance (échelle unique, obligatoire)

| Niveau | Signification |
|---|---|
| 5 | Consensus multi-auteurs + validation quantitative possible |
| 4 | Auteur de référence, règle chiffrée, testable |
| 3 | Auteur crédible, règle qualitative ou contextuelle |
| 2 | Opinion isolée, non contredite |
| 1 | Anecdotique, à valider absolument avant usage |

Une règle de niveau 1 ou 2 **ne peut jamais** être utilisée seule par le moteur : elle doit être
confirmée par simulation ou par convergence avec d'autres sources.

## Traçabilité

Chaque affirmation doit être traçable : **Auteur → Livre → Chapitre → Page**.
Une information sans source est supprimée, jamais conservée « en attendant ».

## Séparation recherche / développement

- Interdit ici : code métier, scripts de trading, notebooks d'implémentation.
- Autorisé : pseudo-code descriptif, formules mathématiques, schémas en texte.

## Cycle de vie d'une connaissance

`EXTRAITE` → `NORMALISÉE` (format officiel) → `DÉDUPLIQUÉE` → `PONDÉRÉE` → `VALIDÉE` (simulation) → `ACTIVE`
ou `REJETÉE` (avec justification conservée). Les statuts sont notés dans le champ *Historique* de chaque règle.
