# TTWO Quantitative Validation V10 — Design de Phase 0

Statut : `draft_to_validate`

Date : 2026-08-08

Branche : `codex/v10-quantitative-validation-and-robust-decision-engine`

Portée exécutée : Phase 0 uniquement

Décision d'implémentation : aucune ; validation utilisateur requise

## Réponse exécutive

Le dépôt est techniquement sain et possède déjà beaucoup plus qu'un prototype : 127 fichiers source suivis, 25 fichiers de tests, 141 tests passants, trois pipelines générationnels, des contrats Pydantic, des connecteurs point-in-time, du pricing Black-Scholes et américain QuantLib, des simulations déterministes, des garde-fous de données, un optimiseur entier, des rapports autonomes et un blocage d'ordre vérifié statiquement.

Le risque dominant n'est donc pas l'absence de modèles. C'est l'absence d'une colonne vertébrale quantitative commune : conventions dispersées, mesure P/Q non typée, diagnostics IV incomplets, validation numérique sans harnais multi-pricer, surface Dupire sans calibration SVI, calibrations empiriques légères, holdout non vierge, registres de formules/expériences absents et schémas/reporting dupliqués entre générations. Ajouter Bergomi, rough volatility ou un taux stochastique maintenant augmenterait la sophistication sans augmenter le niveau de preuve.

La proposition est incrémentale : conserver V7–V10 en lecture/compatibilité, garder V11.1 comme orchestration courante, introduire à partir de la Phase 1 un petit noyau quantitatif partagé et typé, puis migrer les appels un à un avec tests différentiels. `no_trade`, `transmit=false`, `what_if=true`, le mode hors ligne et les rapports autonomes restent des invariants d'architecture.

## 1. Périmètre audité et preuves

### Dépôt

- 454 fichiers suivis ; environ 26 400 lignes dans `src/`, 3 963 dans `tests/`, 2 171 dans `fixtures/`.
- Racines fonctionnelles : `src/take_two_options`, `tests`, `fixtures`, `configs`, `schemas`, `scripts`, `reports`, `experiments/legacy/v7-v9`, `validation`, `docs`.
- Documents lus : `README.md`, `pyproject.toml`, `docs/known_limits.md`, `docs/LIMITATIONS.md`, `docs/rule_status_policy.md`, V1/V2/V7/V8/V9, guides Alpaca/MarketData/IBKR, architecture V10/V11, calibration, backtesting, provenance, risque modèle et contrat produit.
- `docs/testing_strategy.md` demandé par le brief est absent ; seule la version archivée `docs/archive/v9/testing_strategy.md` existe.
- Tous les modules Python et tests ont été inventoriés par AST ; toutes les fixtures ont été hachées et validées par les commandes hors ligne existantes.

### Baseline reproductible

| Contrôle | Résultat Phase 0 |
|---|---|
| `.venv/bin/python -m pytest -q` | 141 passés, 1 avertissement de dépréciation `websockets.legacy` |
| `.venv/bin/ruff check src tests scripts` | passé |
| `.venv/bin/mypy src scripts` | passé, 124 fichiers source |
| `.venv/bin/pip check` | aucune dépendance cassée |
| export des schémas hors ligne | 6 schémas vérifiés |
| validation des artefacts hors ligne | passée ; calibration et walk-forward `fixture-only` |
| garde sécurité | 121 fichiers scannés ; aucun import interdit ; aucun `transmit=True` ; ordre interdit |

Versions installées observées : Python cible `>=3.11`, QuantLib `1.43`, alpaca-py `0.43.5`, NumPy `2.5.1`, Pydantic `2.13.4`, PyYAML `6.0.3`, Typer `0.27.0`, pytest `8.4.2`, Ruff `0.15.22`, mypy `1.20.2`, Hypothesis `6.163.0`.

### Bibliothèque documentaire

Le checkout ne contient pas `BOOK` et Git n'en suit aucun exemplaire. Le corpus demandé a été retrouvé à `/Users/insular/Desktop/book 📙`, alias candidat à confirmer. Il contient 137 PDF, 32 983 pages, les onze fragments Bergomi et les trois fichiers Andersen–Piterbarg. Voir [book_inventory.md](../../research/book_inventory.md), [book_inventory.json](../../research/book_inventory.json) et [source_registry.yaml](../../research/source_registry.yaml).

## 2. Architecture actuelle

```text
                         ┌─ root modules V1/V2/V7-V9 (compatibilité/legacy)
sources/fixtures ────────┼─ thesis_scanner V10 (scan de thèse + dashboard autonome)
                         └─ intelligence V11.1 (data hub → calibration → scénarios
                                                → paths/valuation → allocation
                                                → reporting/readiness)

shared generic path: knowledge schemas → candidate_generation → forecasting/simulation
                     → optimization/validation → decision → reporting

all paths: preview only → transmit=false → what_if=true → NO_TRADE always feasible
```

Les couches ne sont pas simplement des doublons morts : elles conservent des contrats et rapports historiques. Mais plusieurs symboles sont redéfinis (`DecisionReport`, `FundamentalScenario`, `HestonParameters`, `EnumerationResult`, `FreshnessStatus`) et des fonctions utilitaires sont répétées (`_ensure_utc`, `_normal_cdf`, `rank_candidates`, `write_reports`). La migration doit donc être explicite ; supprimer ou fusionner globalement maintenant serait risqué.

### Derniers artefacts par génération

| Génération | Artefact inspecté | Constat |
|---|---|---|
| V9 | `experiments/legacy/v9/reports/ttwo_v9_budget_report.*` | 25 variantes ; `no_trade` premier ; holdout réutilisé/exploratoire ; ordre interdit |
| V10.1 | `reports/examples/v10_thesis_scan.*` | synthétique ; `watchlist` ; 18 candidats ; 3 classements ; probabilités utilisateur, pas estimation empirique |
| V11.1 | `reports/v11/latest.*` | `fixture-only` ; calibration et backtest bloqués faute de données ; promotion fausse ; 15 allocations ; ordre interdit |

La prudence des artefacts est correcte. Leur sémantique de preuve n'est toutefois pas unifiée : schémas `1.0`, `10.1` et `11.1`, catégories de statut différentes et pas d'énumération commune `decision_grade`.

## 3. Constat quantitatif détaillé

### Conventions et mesures

- Le temps jusqu'à expiration utilise `365` jours dans `pricing.py`, `simulation/legacy_models.py`, `intelligence/stochastic.py`, `volatility_calibration.py` et `valuation.py` ; QuantLib utilise `Actual365Fixed` et `NullCalendar`.
- Les rendements historiques utilisent `252` séances dans `calibration.py`, `accuracy.py`, `forecasting/regimes.py` et `intelligence/calibration.py`.
- Theta Black-Scholes est converti par `365`, tandis que les horizons de backtest mêlent séances et jours calendaires. Ces choix peuvent être cohérents, mais ne sont ni centralisés ni portés par un contrat.
- Aucune structure ne type la mesure. `simulation/legacy_models.py` annonce une dérive risque-neutre ; `intelligence/stochastic.py` annonce une dérive réelle configurée. L'hybride trajectoires sous P + repricing sous Q peut être valide, mais il n'est pas protégé contre un branchement incorrect.

### Pricing, IV et surface

- `pricing.black_scholes_price_greeks` fournit prix et Greeks analytiques européens avec unités documentées.
- `american.py` délègue le prix américain à QuantLib FD et calcule ses Greeks par différences finies.
- `historical_option_analytics` résout l'IV américaine par bissection sur `[0.0001, 5]`, 100 itérations et tolérance `1e-6`. Le résultat ne publie ni convergence, ni itérations, ni résidu, ni bracket final, ni cause d'échec structurée.
- Il n'existe pas de harnais central comparant analytique, arbre/binomial, FD et Monte Carlo avec balayage de grille et tolérances par contrat.
- La surface historique interpole linéairement l'IV en strike/échéance et extrapole plat. V11 calcule une local-vol Dupire par différences finies et compte les violations calendar/butterfly, puis retombe sur l'IV des nœuds instables. Aucun ajustement SVI/eSSVI, poids de cotation, RMSE, stabilité multi-start ou garantie globale d'absence d'arbitrage n'existe.

### Calibration, séries temporelles et régimes

- Le legacy estime volatilité réalisée et sauts heuristiques ; Heston est explicitement insuffisant.
- V11 estime drift/vol GBM et sauts à partir de huit observations synthétiques dans l'exemple, avec readiness locale ; il n'exécute pas une calibration Heston complète.
- Aucun EWMA/GARCH/GJR/EGARCH, diagnostic des résidus, conditionnement/Jacobienne/covariance des paramètres ou calibration multi-start.
- Les régimes actifs sont `low/normal/high` sur la volatilité ; les scénarios `neutral/thesis/adverse/rupture` sont configurés, non appris. Il n'existe pas de régimes joints du type tendance/volatilité identifiés hors échantillon.

### Monte Carlo, sorties et incertitude

- Points forts : seeds déterministes, ensembles de chemins distincts, GBM/local-vol/Heston/sauts, revalorisation de legs, règles de sortie, CI de moyenne et contrôle moitié/total.
- Manques : antithétiques, control variates, moment matching, Sobol/QMC, ESS, réplications multi-seed, contrôle explicite des événements rares, block bootstrap, Longstaff–Schwartz et exercice/assignment/dividendes entre checkpoints.
- `research_statistics.wilson_interval` existe et est testé, mais n'est pas utilisé uniformément pour les probabilités V11. Le bootstrap existant est i.i.d.
- `simulation/path_execution.py` remplace silencieusement une IV absente par `0.45`. C'est le défaut le plus dangereux identifié : il peut rendre un résultat calculable sans rendre l'imputation visible dans son grade.

### Backtest, holdout et statistiques de recherche

- Les primitives de purge, embargo, DSR, PBO et manifeste de holdouts contaminés existent.
- V11 modélise train/validation/test/holdout, offres bid/ask point-in-time et baselines, mais les exemples sont synthétiques et ne constituent qu'un seul petit split.
- `final_holdout_locked` et `final_holdout_used_for_tuning: Literal[False]` sont des champs déclaratifs ; aucun journal d'accès, hash immuable, protocole de création ou audit indépendant ne prouve encore un holdout vierge.
- `validation/placebo.py` mélange les rendements puis compare les moyennes. Une permutation conserve exactement la moyenne : ce placebo est mathématiquement non informatif. Les moyennes retardées ne testent pas davantage une hypothèse nulle bien définie.
- Le PBO sélectionne les ex æquo par premier index (`sorted(...).index(...)`) ; l'effet des ties doit être confronté à la définition primaire CSCV.
- Le résumé de gate privilégie parfois `INSUFFICIENT_DATA` malgré une contamination/échec simultané. Les détails restent présents, mais le headline peut sous-communiquer le risque.

### Optimisation et décision

- V11 énumère exactement des quantités entières et contrôle budget, perte maximale, nombre de contrats/positions, concentration, liquidité et Greeks. Cash/`NO_TRADE` est inclus avec objectif zéro.
- L'objectif est explicite mais codé, pas sélectionnable par contrat. La frontière de Pareto générique existe pour les candidats ; l'allocation V11 expose des alternatives classées mais pas une frontière multi-objectifs budget/risque/probabilité/coût.
- Le « bayésien » V11 est une agrégation de scénarios/règles avec probabilités utilisateur et avertit correctement qu'il ne s'agit pas d'intervalles statistiques. Il ne doit pas être présenté comme calibration bayésienne.

### Données et reporting

- V11 possède UTC, cutoff, unités, doublons, checksums et statuts de connecteurs. Il manque un contrat transversal distinguant `observed`, `derived`, `imputed`, `missing` et un score de qualité pour chaque champ critique.
- Les corporate actions, deliverables OCC, multiplicateurs, styles d'exercice et calendriers ne sont pas validés de bout en bout sur chaque chemin d'ingestion.
- `docs/known_limits.md` est court et V10-centré alors que `docs/LIMITATIONS.md` est la limite V11 courante. Cette coexistence est une contradiction documentaire.
- Le README contient de nombreuses formules, mais aucun `formula_id` versionné ne relie source, hypothèses, mesure, unités, code et tests.

## 4. Matrice fonctionnelle

Abréviations de priorité : P0 bloque une interprétation fiable ; P1 forte valeur ; P2 utile après les fondations ; P3 seulement si gain démontré.

| Fonctionnalité | État actuel | Preuve dépôt | Source pertinente | Manque | Modification proposée | Fichiers concernés | Tests nécessaires | Risque régression | Gain attendu | Acceptation | Priorité |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Safety read-only | robuste/testé | `intelligence/execution.py`, `scripts/security_gate.py`, tests preview | OCC ; guides IBKR | aucun blocage majeur | conserver les interdictions comme invariant de CI | sécurité, tickets, CI | AST + artefact `transmit=false` | faible | capital protégé | zéro capacité d'ordre/import/transmit | P0 invariant |
| Provenance données | forte mais locale aux schémas V11 | `intelligence/data_hub.py`, schemas, tests cutoff | Alpaca, MarketData, FRED/ALFRED | pas de statut champ par champ | contrat `ObservedValue`/lineage partagé | `quantitative/contracts.py`, adapters | missing/imputed/cutoff/property tests | moyen | empêche données reconstruites invisibles | tout input quant a source, as-of, unité, statut | P0 |
| Conventions temps/unités | dispersées | recherches `365`, `252`, `Actual365Fixed` | Andersen–Piterbarg ch. 1–6 ; Süli/Mayers | pas de registre central | `QuantConventionSet` injecté et sérialisé | nouveau noyau + adapters existants | identités conversion, golden prices | élevé | supprime erreurs d'échelle | aucune constante annuelle implicite dans calcul public | P0 |
| Séparation P/Q | implicite | `legacy_models.py`, `intelligence/stochastic.py` | Björk ; Andersen–Piterbarg ; Shreve II absent | aucune enum/validation | `Measure=P|Q`, séries et modèles tagués, pont P→Q explicite | stochastic, valuation, pricing | appels incompatibles rejetés | élevé | évite drift erroné | chaque distribution/pricer publie sa mesure | P0 |
| Black-Scholes/Greeks | implémenté/testé | `pricing.py`, `tests/test_pricing.py` | Shreve II à obtenir ; Andersen–Piterbarg 1.9 | pas de cross-pricer central | intégrer au harnais numérique, ne pas réécrire | pricing + numerical validation | put-call parity, limites, Hypothesis | faible | référence analytique fiable | tolérances publiées et passées | P1 |
| Prix américain FD | implémenté via QuantLib | `american.py`, tests historiques | Andersen–Piterbarg ch. 1–2 ; QuantLib 1.43 | convergence/grilles limitées | balayage grid/time, benchmark européen/binomial | american + harness | convergence monotone/tolérances | moyen | confiance numérique | statut par contrat et erreurs bornées | P1 |
| Solveur IV | bissection minimale | `american.historical_option_analytics` | Süli/Mayers ; Nocedal/Wright | diagnostics et bornes incomplets | résultat typé avec bracket/résidu/itérations/échec | american ou shared `implied_volatility.py` | arbitrage bounds, deep ITM/OTM, no root | moyen | refuse IV trompeuse | convergence explicite ou échec bloquant | P0 |
| Surface IV/local vol | interpolation + Dupire diagnostic | `vol_surface.py`, `intelligence/volatility_calibration.py` | Gatheral absent ; Bergomi 4,7–9 | SVI/eSSVI, poids, stabilité, arbitrage global | SVI d'abord ; eSSVI seulement si données suffisantes | shared surface + adapter V11 | synthetic known params, calendar/butterfly, perturbation | élevé | surface stable et explicable | fit/violations/stabilité dans rapport | P1 |
| Calibration GBM/sauts/Heston | partielle/heuristique | `calibration.py`, `intelligence/calibration.py` | Tsay ; Bergomi 6 ; Nocedal/Wright | diagnostics, identifiabilité, multi-start | calibration contract + baselines ; Heston seulement si chaîne riche | calibration modules | recovery synthétique, conditionnement, failure modes | élevé | évite paramètres plausibles mais non identifiés | rapport convergence+incertitude+readiness | P1 |
| Volatilité conditionnelle | absente | aucun GARCH/EWMA | Tsay | baseline récente manquante | EWMA puis GARCH, sélection hors échantillon | future time-series module | simulation/recovery/walk-forward | moyen | forecast P potentiellement meilleur | gain net vs RV baseline sur données PTI | P2 |
| Régimes | heuristique/configuré | `forecasting/regimes.py`, scenario config | Tsay ; McElreath/Särkkä ultérieurs | pas de stabilité/transition apprise | commencer règles transparentes ; HMM seulement si gain | regimes | synthetic, label stability, OOS | moyen | scénarios cohérents | amélioration calibration/decision grade | P2 |
| Génération MC | riche mais non consolidée | simulation packages + `intelligence/stochastic.py` | Glasserman ; Andersen–Piterbarg ch. 3 | réduction variance/ESS/multi-seed | couches de variance reduction optionnelles et benchmarkées | simulation | variance avant/après, seed invariance | moyen | CI plus étroites à coût égal | benchmark reproductible sans biais | P1 |
| Règles de sortie | implémentées par checkpoints | `intelligence/exit_rules.py`, valuation | Glasserman ; Bergomi selon modèle | exercice américain et événements intra-pas | formaliser state machine ; LSM seulement si matériel | exit rules/valuation | path fixtures, boundary cases | élevé | PnL plus réaliste | règles exactement rejouables et coûts inclus | P1 |
| Incertitude MC | CI moyenne basique | valuation + convergence ; Wilson utilitaire | Wasserman ; Glasserman | CI probabilités, ESS, événements rares | métriques typées et réplications multi-seed | uncertainty/convergence/reporting | coverage synthétique, min paths | moyen | décisions graduées | CI + warning rare event pour toute probabilité | P1 |
| Holdout | contaminé/déclaratif | manifest V7–V9, `holdout_locked` | Wasserman ; FRED/ALFRED | aucun nouveau holdout vierge/audit d'accès | protocole + hash + ledger append-only avant tuning | validation/experiment registry | tentative accès/tuning rejetée | très élevé | preuve hors échantillon réelle | dataset neuf scellé et jamais utilisé pour choix | P0 |
| Purge/embargo/walk-forward | primitives présentes | validation + backtesting | Tsay ; sources primaires à ajouter | couverture chronologique incomplète | moteur de splits invariant PTI | backtesting | overlap/property tests | élevé | réduit fuite temporelle | zéro overlap, embargo démontré | P0 |
| Multiple testing | DSR/PBO présents | `research_statistics.py`, `validation/pbo.py` | source primaire manquante | conformité/ties/registry essais | valider définitions, journaliser nombre d'essais | statistics/validation/registry | cas papier, ties, permutation | moyen | contrôle sélection | reproduction des exemples primaires | P1 |
| Placebo | implémenté mais invalide | `validation/placebo.py` | source primaire à sélectionner | permutation conserve la moyenne | redéfinir placebo sur labels/timing/signaux | placebo | null synthetic, power test | moyen | diagnostic réellement informatif | Type-I contrôlé sur null connu | P0 |
| Bayésien | agrégateur heuristique explicite | `intelligence/bayesian.py` | McElreath ; Särkkä | pas d'inférence/posterior predictive | conserver nom/limite ; modèle probabiliste seulement avec data | bayesian/reporting | calibration score, posterior predictive | élevé | incertitude de thèse mieux séparée | aucune probabilité empirique sans calibration | P2 |
| Optimisation budget | exacte et robuste | `intelligence/optimizer.py` | Boyd ; Nocedal | objectif non interchangeable | contrat d'objectif + conserver énumération entière | optimizer/contracts | exhaustive toy oracle, infeasible/no_trade | moyen | arbitrages transparents | optimum reproduit et contraintes tracées | P1 |
| Pareto | candidats oui, allocations non | `optimization/pareto.py`, ranking | Boyd | frontière budget-risque absente | frontier pour solutions réalisables uniquement | optimizer/reporting | dominance/ties/invariance | faible | choix multi-objectif visible | aucune solution dominée au front 1 | P2 |
| Qualité contrat option | partielle | schemas/data hub | OCC ODD + memos contrat | deliverable/style/multiplier non bout-en-bout | `OptionContractTerms` sourcé | data hub/schemas/pricers | split/merger/nonstandard/100x | élevé | empêche payoff faux | inconnu bloque `decision_grade>=validation` | P0 |
| Reporting/grade | autonome mais versionné par génération | V9/V10/V11 reports | politique interne | sémantique de preuve non unifiée | `decision_grade` commun + raisons | schemas/reporting | schema/golden/no network | moyen | empêche confusion synthétique/réel | grade calculé, non saisi, visible partout | P0 |
| Registre formules | absent | README seulement | tous livres + primaires | aucune traçabilité vérifiable | `formula_registry.yaml` + integrity check | docs/research, CI | refs/fichiers/symboles existants | faible | audit scientifique | chaque formule critique a source/code/test | P0 |
| Registre expériences | partiel | manifests/config/seeds dispersés | bonnes pratiques internes | pas commit+dataset+config+trial log unifié | `ExperimentManifest` immuable | validation/reports | hash mismatch, replay | moyen | reproductibilité/multiple testing | replay identique depuis manifest | P0 |
| Readiness empirique | conservatrice mais hétérogène | V11 readiness, limits | politique de statut | champs déclaratifs et statuts multiples | automate de promotion monotone | readiness/schemas | illegal promotion transitions | moyen | niveau de preuve exact | production_ready impossible sans gates | P0 |

## 5. Architecture cible proposée

Cette architecture est une direction à valider, pas une décision d'exécution.

```text
external/local immutable sources
        │
        ▼
existing connectors ──► canonical observed-data contracts
                              │
                              ▼
                    shared quantitative kernel
          conventions │ measures │ IV │ surface │ calibration
          numerical validation │ uncertainty │ experiment manifests
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
        legacy adapters   V10 adapter    V11.1 intelligence
                                               │
                                  allocation + NO_TRADE
                                               │
                         evidence grade + standalone reports
                                               │
                               preview only / order forbidden
```

### Nouveaux contrats proposés

| Contrat | Rôle | Invariant principal |
|---|---|---|
| `QuantConventionSet` | day count, calendrier, annualisation, compounding, monnaie, multiplicateur | chaque calcul public référence une convention sérialisée |
| `MeasureTaggedSeries` | série/rendements/modèle sous P ou Q | conversion implicite interdite |
| `ObservedValue[T]` | valeur, statut observed/derived/imputed/missing, source/as-of/unité | toute imputation est visible et gradée |
| `ImpliedVolResult` | IV + solveur + bracket + résidu + itérations + statut | jamais d'IV nue en cas d'échec |
| `SurfaceFitReport` | paramètres, poids, erreurs, arbitrage, stabilité | aucune surface promue sans diagnostics |
| `CalibrationReport` | objectif, contraintes, starts, convergence, conditionnement, incertitude | paramètres séparés de leur niveau de preuve |
| `ExperimentManifest` | commit, config, dataset hashes, seed, essais, holdout access | replay et multiple testing auditables |
| `DecisionGrade` | invalid/synthetic/screen/research/validation/holdout | promotion calculée par gates monotones |
| `FormulaReference` | formula_id, source, hypothèses, P/Q, unités, code, test | intégrité référentielle en CI |

### Migration sans duplication

1. Ne pas déplacer les modules legacy en Phase 1.
2. Ajouter le noyau partagé derrière des APIs typées.
3. Construire des tests différentiels sur les comportements existants.
4. Migrer V11.1 en premier, un calcul à la fois.
5. Laisser V10 et legacy appeler des adapters tant que leurs golden reports doivent rester reproductibles.
6. Déprécier un symbole dupliqué seulement après preuve d'équivalence et plan de compatibilité de schéma.

## 6. Matrice de recherche documentaire

Chaque cellule « chapitres » est une cible de lecture, pas une provenance déjà validée. Les numéros ne deviennent citables qu'après inspection du passage et enregistrement dans `source_registry.yaml`.

| Chantier | Question quantitative | Livre principal | Livres secondaires | Chapitres à étudier | Outil prévu | Formule/concept recherché | Risques méthodologiques | Validation |
|---|---|---|---|---|---|---|---|---|
| Phase 1 conventions/PQ | quelles conventions et où passe-t-on P→Q ? | Andersen–Piterbarg Vol. I ch. 1, 4, 6 | Björk ; Shreve II à obtenir ; Stewart | mesures, numéraires, day counts, discounting | `runpdf --instruction`, preuve ciblée | change of measure, year fraction, compounding | mélanger drift réel et pricing ; 252/365 | identities + type errors + golden prices |
| Phase 1 audit numérique | quelles tolérances sont défendables ? | Süli/Mayers à confirmer | Strang ; Nocedal ; Andersen–Piterbarg ch. 2 | conditionnement, root finding, FD stability | extraction locale puis `pdf-evidence inspect` | erreur discrétisation, résidu, convergence | fausse précision, cancellation | convergence sweeps multi-pricer |
| Phase 2 IV | comment résoudre et diagnostiquer l'IV robuste ? | Süli/Mayers | Nocedal ; Andersen–Piterbarg 1.9 | bracketing/Newton/bisection | Summarizer ciblé | no-arbitrage bounds, root diagnostics | absence de racine, vega faible | cas synthétiques/limites/propriétés |
| Phase 2 surface | SVI suffit-il à la chaîne TTWO ? | Gatheral **absent** | Bergomi ch. 4, 7–9 ; Nocedal | SVI, total variance, arbitrage | source à obtenir + fragments Bergomi | raw/natural SVI, constraints | sparse quotes, extrapolation, local minima | recovery + static arbitrage + perturbation |
| Phase 3 séries/calibration | EWMA/GARCH/Heston apportent-ils un gain ? | Tsay | Bergomi ch. 6 ; Nocedal ; Wasserman | GARCH diagnostics, Heston identifiability | `runpdf` ciblé | likelihood, residuals, parameter covariance | breaks, non-identifiability | rolling OOS vs baselines |
| Phase 4 backtest/holdout | quel protocole évite fuite et sélection ? | Wasserman | Tsay ; sources primaires CSCV/DSR | tests, bootstrap, model selection | livre + primaires officielles/papers | purge, embargo, PBO, DSR | holdout déjà vu, revisions macro | sealed new dataset + audit ledger |
| Phase 5 MC/sorties | comment simuler le path-dependent sans biais inutile ? | Glasserman | Andersen–Piterbarg ch. 3 ; Bergomi ch. 3 | variance reduction, stopping, LSM | `runpdf` + preuve formule | antithetic/control, stopping rule | look-ahead, American exercise, discretization | analytic toys + multi-seed convergence |
| Phase 6 incertitude/Bayes | quelles incertitudes peuvent être propagées ? | McElreath | Wasserman ; Särkkä ultérieur | posterior predictive, shrinkage | `runpdf` ciblé | model averaging/parameter uncertainty | priors dominate sparse data | calibration scores + posterior predictive |
| Phase 7 budget/Pareto | quelle fonction objectif est utile avec contrats entiers ? | Boyd & Vandenberghe | Nocedal | KKT, robust optimization, Pareto | `runpdf` ciblé | dominance, utility, robust constraints | relaxation non réalisable, faux optimum | exhaustive toy oracle + frontier invariants |
| Phase 8 événements | comment mettre à jour une thèse sans double compter ? | McElreath | Särkkä ; Blitzstein/Hwang | Bayes conditionnel, filtering | `runpdf` ciblé | likelihood ratios/state update | causalité, dépendance, overconfidence | synthetic event sequences + calibration |
| Phase 9 reporting | comment exprimer un niveau de preuve ? | Wasserman | OCC ; politique interne | intervalles/tests/communication | lecture ciblée | decision grade, uncertainty wording | conseil implicite, confusion synthétique | schema + golden report review |
| Phase 11 extensions | Bergomi/taux avancés changent-ils matériellement TTWO ? | Bergomi tous fragments ; Andersen–Piterbarg | Glasserman ; Nocedal ; Gatheral à obtenir | forward variance, rates, calibration | recherche multi-PDF | incremental value vs Heston/curve simple | sophistication non identifiable | ablation OOS, ranking sensitivity, cost benchmark |

## 7. Données qui ne permettent pas une validation sérieuse aujourd'hui

1. **Nouveau holdout TTWO** : aucun dataset vierge, scellé et jamais consulté n'existe.
2. **Historique options riche** : l'API Alpaca officielle n'annonce des options historiques que depuis février 2024 ; les fixtures locales sont synthétiques et minuscules. Cela ne couvre pas plusieurs cycles/régimes.
3. **Intraday options et exécution** : MarketData documente des chaînes historiques EOD mais pas d'historique options intraday. Slippage, partial fills et timing des règles de sortie ne sont pas validables avec les seules chaînes EOD.
4. **Entitlements/live feeds** : OPRA/IBKR live n'ont pas été exercés en Phase 0 ; les droits, latences et quotas réels restent inconnus.
5. **Corporate actions/adjusted contracts** : aucun corpus exhaustif de memos OCC et deliverables TTWO point-in-time n'est fourni.
6. **Assignment/early exercise** : aucune observation d'assignation, de borrow, de dividendes discrets et de décision intra-journalière.
7. **Événements GTA6** : trop peu d'événements indépendants pour estimer sérieusement des probabilités conditionnelles fines ou un effet causal.
8. **Heston/Bergomi/rough vol** : une chaîne sparse autour d'un seul sous-jacent ne permet pas d'établir identifiabilité, stabilité et gain hors échantillon.
9. **Régimes macro** : sans données vintage-aware ALFRED, les backtests macro risquent d'utiliser des révisions futures.
10. **Taux stochastiques** : la matérialité sur le classement de stratégies TTWO à DTE borné n'est pas démontrée ; un modèle complexe ne serait pas empiriquement validable.

Toute sortie issue de ces données doit rester au plus `synthetic`, `screen` ou `research`, jamais `holdout_validated`/`production_ready`.

## 8. Améliorations séduisantes à ne pas implémenter maintenant

| Idée | Pourquoi séduisante | Pourquoi probablement inutile maintenant | Gate avant réexamen |
|---|---|---|---|
| Bergomi/rough Bergomi | dynamique de smile riche | données sparse, calibration coûteuse, Heston non encore validé | gain OOS et sensibilité de classement vs Heston |
| Taux stochastiques/HJM | théorie complète | DTE et exposition taux probablement faibles | variation matérielle du prix/rang vs courbe déterministe |
| eSSVI immédiat | cohérence inter-échéances élégante | SVI simple et qualité des quotes non validés | SVI insuffisant sur chaîne nettoyée |
| HMM/ML de régimes | transitions apprises | peu de régimes/événements, instabilité des labels | amélioration OOS stable vs règles simples |
| Bayésien hiérarchique complet | shrinkage et incertitude | population d'événements trop petite | posterior predictive calibré et données multi-actifs justifiées |
| Longstaff–Schwartz partout | exercice américain en MC | coût/complexité, moteur FD déjà présent | biais de checkpoints matériel sur contrats ciblés |
| Greeks d'ordre élevé/AAD | gestion fine du risque | outil read-only, petit budget, pas d'exécution | besoin décisionnel mesuré et benchmark de stabilité |
| Sobol/QMC distribué | vitesse/convergence | convergence et variance reduction basiques non instrumentées | baseline profilée et gain reproductible |
| Neural vol surface | flexibilité | opacité, données insuffisantes, arbitrage difficile | corpus multi-régime et benchmark SVI battu |

## 9. Validité externe vérifiée au 2026-08-08

Audit ciblé de sources primaires/officielles, sans appel de données de marché :

- QuantLib 1.43 est la release officielle observée et correspond exactement au pin/install local : [release 1.43](https://github.com/lballabio/QuantLib/releases/tag/v1.43), [documentation officielle](https://www.quantlib.org/docs.shtml).
- Alpaca distingue OPRA et un feed indicatif qui n'est pas une cotation OPRA réelle, et annonce l'historique options depuis février 2024 : [Historical Option Data](https://docs.alpaca.markets/us/docs/historical-option-data).
- MarketData expose une chaîne courante ou historique EOD : [Option Chain API](https://www.marketdata.app/docs/api/options/chain/). Sa page produit indique ne pas offrir l'historique options intraday.
- IBKR indique que la plupart des titres exigent un abonnement Level 1 pour les données API : [Market Data Subscriptions](https://www.interactivebrokers.com/docs/general/market-data-subscriptions/introduction).
- L'OCC conserve l'ODD June 2024 comme version de distribution visible et rappelle les ajustements contractuels : [OCC ODD](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document).
- FRED/ALFRED distingue date d'observation et période réelle de connaissance ; le défaut représente l'information connue aujourd'hui : [Real-Time Periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html).
- Le Treasury signale une rupture méthodologique le 2021-12-06 vers une spline monotone convexe : [Daily Treasury Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_).

Limite : ce contrôle confirme les contrats/documentations visibles, pas les credentials, entitlements, quotas, réponses réelles ni la qualité des données TTWO.

## 10. Contradictions et erreurs actives

1. `BOOK` est absent du repo alors que le brief le décrit comme partie intégrante ; un alias local probable existe.
2. Aucun outil autonome `Transcript` n'est installé ; la transcription est une capacité du projet Summarizer.
3. Les trois PDF `interest rate` ne sont pas trois volumes complets : deux forment le Volume I, un le Volume II, le Volume III manque.
4. Le brief demande un design « V10 », mais le HEAD et les rapports courants sont V11.1 ; le nom de fichier est conservé pour compatibilité, pas pour rétrograder l'architecture.
5. `docs/testing_strategy.md` manque ; la stratégie V9 archivée ne décrit pas toute la baseline V11.
6. `docs/known_limits.md` et `docs/LIMITATIONS.md` se chevauchent avec des périmètres différents.
7. Les trajectoires legacy Q et V11 P coexistent sans tag de type.
8. Une IV absente peut devenir silencieusement `0.45` dans l'exécution de chemins.
9. Le placebo par permutation compare des moyennes identiques par construction.
10. Les champs de lock/usage holdout décrivent un état mais ne le prouvent pas.
11. Le Wilson interval existe déjà ; le réimplémenter serait un doublon. Il faut le raccorder aux métriques concernées.
12. Les frontières de Pareto existent déjà pour les candidats ; la Phase 7 doit étendre l'allocation, pas recréer l'algorithme de dominance.

## 11. Ordre final proposé et gates

L'ordre obligatoire 0–11 est conservé, avec une règle supplémentaire : le protocole du nouveau holdout doit être figé dès la Phase 1 et le dataset scellé avant toute sélection de méthode en Phase 2–3, même si son évaluation finale appartient à la Phase 4.

1. **Phase 0 — audit/inventaire/spec** : présente modification ; arrêt après validation.
2. **Phase 1 — conventions, P/Q, audit numérique** : fondations, contrats, harnais et registre formules.
3. **Phase 2 — IV et SVI** : SVI avant eSSVI ; aucune promotion sans quotes suffisantes.
4. **Phase 3 — calibration et séries temporelles** : baselines simples avant Heston/GARCH avancé.
5. **Phase 4 — backtest et holdout** : purge/embargo, registry, lock et première ouverture contrôlée.
6. **Phase 5 — Monte Carlo des sorties** : réduction de variance, probabilités/CI, state machine ; LSM conditionnel.
7. **Phase 6 — incertitude/Bayes** : seulement sur paramètres identifiables.
8. **Phase 7 — budget/Pareto** : conserver l'énumération entière ; objectifs comparables.
9. **Phase 8 — événements/séquentiel** : mises à jour calibrées, pas de causalité implicite.
10. **Phase 9 — rapport/dashboard/docs** : grade commun, formule→source→code→test.
11. **Phase 10 — validation intégrale** : full suite, replay, limits, sécurité, performance.
12. **Phase 11 — évaluation avancée** : Bergomi, rough vol, filtering, taux ; implémentation uniquement après preuve de gain matériel.

### Gate commun à chaque phase quantitative

- `Documentary Research` renseignée avec passages réels ;
- source, hypothèses, mesure et unités enregistrées ;
- changement borné et migration explicitée ;
- tests unitaires, propriétés, régression et exemple synthétique ;
- exemple réel seulement si les données satisfont le grade ;
- limites et statut de preuve mis à jour ;
- aucune régression safety/read-only/no_trade ;
- commit atomique ;
- arrêt si un gate échoue.

## 12. Critères d'acceptation de la Phase 0

- les cinq livrables demandés existent et leurs JSON/YAML sont valides ;
- les 138 chemins documentaires sont inventoriés ;
- Bergomi et Interest Rate Modeling sont regroupés correctement ;
- les métadonnées inconnues restent `null`/`unknown` ;
- la syntaxe réelle de Summarizer est enregistrée et l'absence de Transcript autonome est visible ;
- la matrice fonctionnelle et la matrice documentaire sont complètes ;
- aucune méthode quantitative ni module métier n'est modifié ;
- la baseline tests/lint/mypy/sécurité reste verte ;
- l'architecture, les risques, les données insuffisantes et les refus de sophistication sont explicites ;
- la suite des phases reste bloquée jusqu'à validation utilisateur.

## 13. Décisions demandées

Avant Phase 1, valider explicitement :

1. que `/Users/insular/Desktop/book 📙` est bien l'alias opérationnel de `BOOK` ;
2. que V11.1 reste l'orchestrateur courant et que le noyau partagé est la trajectoire de convergence ;
3. que le placebo actuel est classé `invalid` jusqu'à remplacement ;
4. que le protocole de holdout doit être figé/scellé avant tout tuning des Phases 2–3 ;
5. que Gatheral et Shreve II doivent être obtenus, ou remplacés par des sources primaires autorisées, avant les chantiers concernés ;
6. que Bergomi, rough volatility et taux stochastiques restent en évaluation Phase 11.

Aucune de ces propositions n'est une décision d'exécution tant qu'elle n'est pas validée.
