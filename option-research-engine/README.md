# Investment Call Optimizer — Repository de recherche

> **Statut : PHASE DE RECHERCHE — AUCUN CODE METIER NE DOIT ETRE ECRIT DANS CE DOSSIER.**

L'implementation read-only vit a la racine dans `src/take_two_options/`. La recherche de ce
dossier alimente son registre d'architectures, mais ne vaut jamais validation de strategie.

## Mission

Ce repository est la **base scientifique** du futur moteur d'optimisation d'options (Calls).
Il n'est pas un projet logiciel : c'est un **projet de recherche** dont l'unique objectif est de préparer
le terrain pour que **Codex** puisse développer le moteur en lisant ce repository presque exclusivement.

Le futur moteur devra :

- comparer automatiquement toutes les options disponibles ;
- optimiser le ratio rendement / risque ;
- appliquer uniquement des règles extraites de la littérature spécialisée ;
- utiliser Monte Carlo et des scénarios déterministes ;
- construire un score objectif, explicable et reproductible ;
- gérer automatiquement une position après achat (maintenance) ;
- préparer les ordres Interactive Brokers (IBKR), sans jamais les envoyer sans validation humaine.

## Principe fondamental

> Le moteur ne cherche pas le Call qui « paraît » le meilleur.
> Il cherche la stratégie qui **maximise l'espérance de gain ajustée du risque**, selon les règles
> issues de la littérature, les données de marché et les simulations.

Corollaires non négociables :

1. **Aucune règle arbitraire.** Toute règle doit provenir d'une source documentée (livre, paper, repo étudié), être traçable (auteur / chapitre / page) et validable par simulation.
2. **Aucune structure imposée a priori.** Le moteur ne doit jamais être forcé de proposer « 1 à 3 Calls » selon une logique fixe « proche / moyen / éloigné ». Il analyse toutes les combinaisons disponibles et propose la ou les meilleures structures (1 Call, 2 Calls, 3 Calls, ITM/ATM/OTM, spread, ou toute autre structure jugée supérieure par les règles extraites). Voir `decision_engine/01_selection_strategie.md`.
3. **Toute décision doit être explicable** : règles utilisées, scores, hypothèses, simulations.
4. **Séparation stricte recherche / développement.** Le code sera écrit plus tard, ailleurs, par Codex.

## Carte du repository

| Dossier | Rôle |
|---|---|
| `docs/` | Documentation transverse : méthodologie de recherche, pipeline d'extraction, moteur de maintenance, onboarding Codex |
| `CHANGELOG.md` | Historique des évolutions documentaires et décisions encore ouvertes |
| `tool_usage.md` | Rôle exact de Gemini, Codex, IBKR, transcript/PDF tooling et repositories open source |
| `evidence/` | Dossiers de preuve par décision : sources, règles, contradictions, simulations favorables/défavorables |
| `research/` | Travaux de recherche en cours + `research/benchmarks/` (analyse des repos open source) |
| `books/` | Bibliothèque officielle : une fiche par livre avec prompt Gemini spécifique |
| `prompts/` | Prompts Gemini par catégorie de connaissance |
| `schemas/` | Contrats JSON canoniques pour la transcription et la revue visuelle |
| `knowledge_base/` | Base de connaissances consolidée (règles fusionnées, pondérées, dédupliquées) |
| `rules/` | Règles atomiques extraites, au format officiel (`rules/FORMAT_REGLE.md`) |
| `simulations/` | Spécifications des simulations (Monte Carlo, scénarios déterministes) |
| `validation/` | Protocoles de validation des règles (out-of-sample, walk-forward, stress tests) |
| `benchmarks/` | Résultats comparatifs entre stratégies et implémentations |
| `decision_engine/` | Spécification documentaire complète du futur moteur de décision |
| `scoring/` | Spécification du moteur de scoring |
| `monte_carlo/` | Connaissances et spécifications Monte Carlo |
| `risk/` | Règles et connaissances de gestion du risque |
| `greeks/` | Règles et connaissances liées aux Greeks |
| `volatility/` | Règles et connaissances liées à la volatilité (IV, HV, IV Rank, IV Crush…) |
| `money_management/` | Sizing, Kelly, récupération du capital, drawdown |
| `psychology/` | Biais cognitifs → garde-fous automatiques |
| `valuation/` | Valorisation, attentes implicites, DCF, multiples |
| `backtesting/` | Méthodologie de backtesting et robustesse |
| `examples/` | Cas pratiques complets, chiffrés, traçables |
| `references/` | Bibliographie, papers, liens, citations |
| `templates/` | Modèles officiels (fiche livre, règle, fiche repository, journal de décision) |

## Ordre de lecture recommandé (pour Codex)

1. `docs/05_onboarding_codex.md`
2. `tool_usage.md`
3. `evidence/README.md`
4. `rules/FORMAT_REGLE.md`
5. `docs/04_ponderation_des_regles.md`
6. `docs/01_methodologie_recherche.md`
7. `decision_engine/` (dans l'ordre des fichiers numérotés)
8. `docs/06_moteur_maintenance.md`
9. `knowledge_base/README.md`
10. `research/benchmarks/`

Pour implémenter ou auditer la transcription PDF, lire également :

11. `docs/07_transcription_pdf_technique_v2.md`
12. `docs/08_plan_implementation_transcription_v2.md`
13. `schemas/README.md`
14. `validation/pdf_transcription_v2_tests.md`

## Règles de contribution

- Toute connaissance ajoutée doit respecter `CONVENTIONS.md`.
- Toute règle doit respecter le format officiel de `rules/FORMAT_REGLE.md`.
- Aucun résumé de livre. Uniquement des règles exploitables.
- Le repository doit pouvoir accueillir plusieurs centaines de livres sans restructuration.
