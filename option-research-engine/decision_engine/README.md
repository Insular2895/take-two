# decision_engine/ — Spécification documentaire du moteur de décision

## Rôle
Décrire entièrement, **sans aucun code**, comment le futur moteur choisit, compare, simule,
score et classe les stratégies d'options.

## Contenu
| Fichier | Contenu |
|---|---|
| `01_selection_strategie.md` | Génération des candidats, règle fondamentale de non-imposition de structure |
| `02_comparaison_options.md` | Comparaison objective des options et combinaisons |
| `03_monte_carlo.md` | Usage de Monte Carlo dans la décision |
| `04_scoring.md` | Construction du score final |
| `05_conflits_et_vote.md` | Gestion des conflits entre règles, vote multi-livres |
| `06_classement.md` | Classement et présentation des stratégies |

## Format attendu
Spécifications en Markdown. Pseudo-code descriptif autorisé, code interdit.

## Dépendances
`rules/`, `knowledge_base/`, `scoring/`, `monte_carlo/`, `simulations/`, `docs/04_ponderation_des_regles.md`.
