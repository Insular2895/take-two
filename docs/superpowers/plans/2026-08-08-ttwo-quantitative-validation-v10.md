# Plan TTWO Quantitative Validation V10

Statut : `in_progress_phase_7_implemented`

Date : 2026-08-08

Branche de travail : `codex/v10-quantitative-validation-and-robust-decision-engine`

Document de design : [2026-08-08-ttwo-quantitative-validation-v10-design.md](../specs/2026-08-08-ttwo-quantitative-validation-v10-design.md)

## Règles d'exécution

- Ne pas démarrer la Phase 1 avant validation explicite de la Phase 0.
- Commencer toute phase quantitative par sa section `Documentary Research` complétée avec passages réels.
- Ne jamais modifier, déplacer ou réparer les PDF sources.
- Ne jamais créer de capacité d'ordre ; préserver `transmit=false`, `what_if=true` et `NO_TRADE`.
- Travailler par petits adapters/tests différentiels ; ne pas réécrire les générations historiques.
- Ne jamais promouvoir `implemented` en `numerically_validated`, `empirically_validated` ou `holdout_validated` sans la preuve correspondante.
- Faire un commit atomique par phase et arrêter si ses gates échouent.

## Phase 0 — Audit, inventaire BOOK et spécification

État : terminé et validé par l'utilisateur le 2026-08-08.

### Documentary Research

- Questions étudiées : localisation/résolution de `BOOK`, intégrité des PDF, œuvres fragmentées, syntaxe réelle des outils, couverture documentaire des futurs chantiers.
- Livres/PDF consultés : préface et table des matières Andersen–Piterbarg ; premières pages des onze fragments Bergomi ; métadonnées des références prioritaires.
- Outils : `find`, `file`, `mdls`, `qpdf`, SHA-256, Ghostscript, Tesseract, `./runhelp`, `./runpdf --help`, `./pdf-evidence --help`.
- Concepts retenus : corpus/œuvre distinct du fichier, provenance par hash, page PDF distincte de la page imprimée, résumé distinct de la preuve.
- Formules retenues : aucune ; Phase 0 n'autorise pas une extraction/implémentation quantitative.
- Contradictions : `BOOK` absent du repo ; alias local retrouvé ; Transcript autonome absent ; Interest Rate Modeling local incomplet.
- Choix proposé : reconnaître l'alias local après confirmation, conserver les PDF read-only, exiger une preuve ciblée avant chaque formule.
- Formula IDs : placeholders uniquement dans `source_registry.yaml`; aucun passage encore promu.
- Fichiers d'implémentation : aucun module métier.
- Tests : validation JSON/YAML/links, baseline complète et diff scope.

### Tâches

- [x] Auditer Git, l'arbre, les générations, docs, sources, tests, fixtures et trois derniers artefacts.
- [x] Exécuter pytest, Ruff, mypy, `pip check`, validation hors ligne et sécurité.
- [x] Localiser le corpus candidat et inventorier récursivement 138 fichiers.
- [x] Hacher les PDF, compter 32 983 pages, détecter les doublons et vérifier l'intégrité.
- [x] Reconstruire Bergomi en une œuvre, chapitres 3–12 + référence.
- [x] Reconstruire Andersen–Piterbarg : Volume I en deux fichiers + Volume II ; Volume III absent.
- [x] Vérifier la syntaxe Summarizer et constater l'absence de Transcript autonome.
- [x] Créer inventaires, registre des sources, design et présent plan.
- [x] Valider les formats structurés et les références de fichiers.
- [x] Rejouer la baseline après documentation.
- [x] Faire le commit atomique de Phase 0.
- [x] Obtenir la validation utilisateur et s'arrêter.

### Acceptation

- cinq livrables valides ; inventaire complet ; aucune métadonnée inventée ; matrices et risques présents ; aucun module métier modifié ; baseline verte ; aucune Phase 1 exécutée.

## Gate préalable aux Phases 1–4 — protocole de holdout

Le protocole, l'identifiant et le hash du nouveau holdout doivent être définis/scellés avant le premier choix de méthode ou réglage des Phases 2–3. Son contenu ne doit pas être ouvert. La Phase 4 implémentera et auditera son usage final. Ce gate évite de fabriquer un « nouveau » holdout après avoir vu les résultats.

Livrables proposés après validation :

- manifeste de dataset immuable ;
- ledger d'accès append-only ;
- politique de séparation train/validation/test/final holdout ;
- règle de rotation/expiration ;
- preuve que les hashes V7–V9 restent contaminés et inéligibles.

## Phase 1 — Conventions, P/Q et audit numérique

État : implémenté ; gate complet vert (146 tests) ; commit `ba8c335`.

### Documentary Research

- Questions : day count/annualisation/compounding ; unités Greeks/PnL ; frontière P→Q ; tolérances de pricers et solveurs.
- Principal : Andersen–Piterbarg Vol. I ch. 1, 2, 4, 6.
- Secondaires : Björk ; Süli/Mayers à confirmer ; Strang ; Nocedal/Wright ; Shreve II à obtenir.
- Outil : `runpdf --instruction` sur les chapitres ciblés, puis `pdf-evidence inspect` pour toute formule ambiguë.
- Concepts/formules : mesure martingale, discount factors, year fractions, conditionnement, erreur FD, convergence.
- Risques : mélanger 252/365 ; dérive P dans un pricer Q ; tolérance absolue trompeuse.
- Validation : identités analytiques, property tests, cross-pricer et balayages de grilles.
- Formula IDs : `FORM-MEASURE-CHANGE-001`, `FORM-BS-PRICE-001`, `FORM-FD-CONVERGENCE-001`, `FORM-DISCOUNT-FACTOR-001`.

### Implémentation proposée

1. Ajouter des contrats immuables `QuantConventionSet`, `Measure`, `ObservedValue`.
2. Ajouter un harnais de validation numérique sans remplacer les pricers.
3. Adapter d'abord V11, puis exposer des wrappers legacy.
4. Créer `docs/math/README.md`, registre formules et `docs/testing_strategy.md` courant.
5. Sceller le protocole du nouveau holdout sans ouvrir son contenu.

### Tests/gates

- conversions jours/séances, annualisation et compounding ;
- P/Q incompatible rejeté au runtime/validation ;
- Black-Scholes vs QuantLib européen ; put-call parity et limites ;
- FD américain : convergence temps/espace et statut explicite ;
- aucune différence dans les golden reports hors nouveaux champs versionnés ;
- sécurité/read-only complète.

Commit proposé : `feat(quant): centralize conventions measures and numerical audit`

## Phase 2 — Solveur IV et surface SVI/eSSVI

État : implémenté ; eSSVI différé derrière le gate ; gate complet vert (152 tests) ; commit
`32f3222`.

### Documentary Research

- Questions : bornes d'arbitrage, root finding à vega faible, choix SVI, contraintes calendar/butterfly, extrapolation.
- Principal : Gatheral à obtenir ; à défaut, papiers SVI/eSSVI primaires validés.
- Secondaires : Süli/Mayers ; Nocedal/Wright ; Bergomi ch. 4, 7–9 ; Andersen–Piterbarg ch. 8–9.
- Outil : Summarizer ciblé + inspection visuelle des formules et pages.
- Alternatives : SVI par échéance ; eSSVI global ; interpolation actuelle comme baseline explicite.
- Risques : minima locaux, quotes sparse, surface lisse mais arbitrageable, extrapolation cachée.
- Validation : paramètres synthétiques connus, stress de quotes, invariants d'arbitrage, stabilité multi-start.

### Implémentation proposée

1. Introduire `ImpliedVolResult` et remplacer la valeur nue dans les nouveaux appels.
2. Conserver bissection comme fallback robuste, ajouter diagnostics/bracket/résidu.
3. Implémenter SVI minimal pondéré et un rapport de fit.
4. N'évaluer eSSVI que si le nombre d'échéances et la qualité des quotes atteignent un gate défini.
5. Interdire toute fallback IV `0.45` silencieuse ; l'imputation doit dégrader le grade.

### Tests/gates

- sous/sur bornes, deep ITM/OTM, maturité courte, vega quasi nulle ;
- reconstruction SVI synthétique, arbitrage, perturbation, reproductibilité ;
- benchmark contre la surface actuelle ;
- aucun gain revendiqué sans chaîne TTWO point-in-time suffisante.

Commit proposé : `feat(quant): add diagnosed iv solving and svi surface validation`

## Phase 3 — Calibration robuste et séries temporelles

État : baselines EWMA/GARCH diagnostiquées et comparaison OOS synthétique implémentées ; Heston
bloqué par le gate de données ; gate complet vert (156 tests) ; commit `3d72715`.

### Documentary Research

- Questions : baseline RV/EWMA/GARCH ; innovations ; diagnostics ; Heston identifiabilité ; multi-start et incertitude paramètres.
- Principal : Tsay ; Bergomi ch. 6.
- Secondaires : Nocedal/Wright ; Wasserman ; Andersen–Piterbarg ch. 8–9.
- Concepts : likelihood, residual tests, stationarity, parameter covariance, profile/multi-start stability.
- Risques : breaks, overfit, contraintes Heston, données options insuffisantes.
- Validation : recovery synthétique puis rolling OOS contre naïf/RV/EWMA.

### Implémentation proposée

1. Standardiser `CalibrationReport`.
2. Ajouter d'abord EWMA comme baseline ; GARCH seulement avec diagnostics.
3. Ajouter multi-start/conditionnement aux calibrations qui le nécessitent.
4. Maintenir Heston `blocked` si la chaîne ne permet pas l'identification.

### Tests/gates

- récupération paramètres synthétiques ; erreurs explicites ; déterminisme ;
- residual diagnostics ; stabilité par fenêtre ; comparaison OOS ;
- aucune promotion pour huit observations synthétiques.

Commit proposé : `feat(quant): add calibration diagnostics and volatility baselines`

## Phase 4 — Protocole de backtest et nouveau holdout

État : protocole, manifests, split point-in-time, placebo corrigé, ex æquo PBO et ledger
implémentés ; holdout réel absent/non ouvert ; gate complet vert (164 tests) ; commit `41fb2f9`.

### Documentary Research

- Questions : split point-in-time, purge/embargo, CSCV/PBO/DSR, placebo, accès holdout.
- Principal : Wasserman ; sources primaires PBO/DSR/CSCV à enregistrer.
- Secondaires : Tsay ; FRED/ALFRED official docs.
- Risques : leakage, revisions, multiple testing, ex æquo, holdout indirectement consulté.
- Validation : jeux synthétiques avec fuite connue, exemples primaires et ledger d'accès.

### Implémentation proposée

1. `ExperimentManifest` avec commit/config/dataset/seed/trial hashes.
2. Split engine avec invariants chronologiques, purge et embargo.
3. Remplacer le placebo de moyenne par un test nul sur labels/timing/signaux.
4. Vérifier PBO/DSR contre les sources primaires, y compris ties.
5. Ouvrir le holdout scellé une seule fois selon le protocole validé.

### Tests/gates

- overlaps impossibles ; données post-cutoff rejetées ;
- placebo à Type-I contrôlé et puissance sur signal synthétique ;
- holdout access écrit dans le ledger et bloque tout tuning ultérieur ;
- V7–V9 restent contaminés.

Commit proposé : `feat(validation): seal experiments and enforce point-in-time holdouts`

## Phase 5 — Monte Carlo des règles de sortie

État : state machine et diagnostics d'incertitude implémentés ; LSM différé faute d'écart
matériel mesuré ; gate complet vert (173 tests) ; commit `7488f5e`.

### Documentary Research

- Questions : biais de discrétisation, stopping rules, variance reduction, CI de probabilités, événements rares, exercice américain.
- Principal : Glasserman.
- Secondaires : Andersen–Piterbarg ch. 3 ; Bergomi ch. 3 ; papier Longstaff–Schwartz local.
- Risques : look-ahead, double-counting des coûts, pseudo-convergence, path reuse.
- Validation : options/jouets analytiques, réplications multi-seed, variance avant/après.

### Implémentation proposée

1. Formaliser les sorties en state machine sérialisable.
2. Ajouter antithétiques et control variate en options mesurables.
3. Ajouter CI Wilson/binomiale, ESS et minimum paths aux probabilités.
4. Ajouter block bootstrap pour séries dépendantes.
5. Évaluer LSM seulement si l'écart FD/checkpoint est matériel.

Commit proposé : `feat(simulation): validate path exits and monte carlo uncertainty`

## Phase 6 — Incertitude de modèle et bayésien

État : croyance heuristique renommée sémantiquement sans rupture de schéma ; ensembles
modèle/paramètres et diagnostics de calibration implémentés ; modèle bayésien statistique
différé faute de likelihood/outcomes explicites ; gate complet vert (177 tests) ; commit
`fc00bc4`.

### Documentary Research

- Questions : propagation paramètre/modèle, priors justifiables, calibration probabiliste, posterior predictive.
- Principal : McElreath.
- Secondaires : Wasserman ; Särkkä uniquement si état latent justifié.
- Risques : priors dominants, double emploi du mot « confiance », événements non indépendants.
- Validation : calibration curves, scoring rules, posterior predictive et ablations.

### Implémentation proposée

1. Renommer/clarifier l'agrégateur heuristique actuel sans casser le schéma.
2. Propager ensembles de paramètres/modèles dans la valuation.
3. N'ajouter un modèle bayésien statistique qu'avec données et likelihood explicites.

Commit proposé : `feat(uncertainty): separate heuristic belief from calibrated model uncertainty`

## Phase 7 — Optimisation budget et frontière de Pareto

État : contrats d'objectif versionnés, oracle entier conservé et frontière exhaustive
non dominée avec cash/NO_TRADE implémentés ; gate complet vert (180 tests) ; commit atomique
`a35fa52`.

### Documentary Research

- Questions : objectifs compatibles avec contrats entiers, robustesse aux distributions, dominance et utility.
- Principal : Boyd & Vandenberghe.
- Secondaire : Nocedal/Wright.
- Risques : relaxation fractionnaire irréalisable, objective hacking, probabilités non calibrées.
- Validation : exhaustive oracle sur petits cas, contraintes et front de dominance.

### Implémentation proposée

1. Conserver l'énumération entière actuelle comme oracle/canonical pour petit budget.
2. Ajouter un contrat d'objectif sélectionnable et versionné.
3. Produire une vraie frontière allocation rendement/risque/coût, toujours avec cash/NO_TRADE.

Commit proposé : `feat(optimization): expose robust integer objectives and pareto allocations`

## Phase 8 — Scénarios événementiels et décision séquentielle

État : contrats point-in-time, dépendances déclarées, origines de probabilités, scénarios de chocs,
sensibilité des croyances et règles advisory implémentés ; tests ciblés verts ; commit atomique à
créer.

### Documentary Research

- Questions : mise à jour conditionnelle, dépendance entre sources, état latent, causalité vs association.
- Principal : McElreath.
- Secondaires : Blitzstein/Hwang ; Särkkä.
- Risques : double comptage, probabilités narratives, très petit n GTA6.
- Validation : séquences synthétiques, calibration, ordre des événements et contradictions.
- PDF : Blitzstein/Hwang ch. 2 pp. 45–79 ; McElreath ch. 5–6 pp. 132–193 ciblées.
- Concepts : indépendance conditionnelle, mise à jour séquentielle, DAG/confounding, mélange de
  scénarios, seuil d'indifférence.
- Formules : `FORM-SCENARIO-MIXTURE-001`, `FORM-BELIEF-SWITCH-001`.
- Hypothèses : graphe acyclique point-in-time, dépendances et remises déclarées, P/Q inchangée.
- Alternatives refusées : naive Bayes, causalité GTA VI et filtre latent sans données identifiantes.
- Limitations : aucune probabilité/choc TTWO réel calibré ; intervalles utilisateur = sensibilité.
- Fichiers : `intelligence/sequential_decision.py`, `intelligence/event_scenarios.py`.
- Tests : `tests/test_sequential_event_decision.py`.

### Implémentation proposée

1. Établir un contrat d'évidence événementielle point-in-time.
2. Rendre les dépendances/corrélations explicites.
3. Garder les probabilités utilisateur distinctes des probabilités calibrées.

Commit proposé : `feat(decision): make event updates sequential and evidence graded`

## Phase 9 — Rapport final, dashboard et documentation

### Documentary Research

- Questions : communiquer incertitude, grade et limites sans produire un conseil garanti.
- Principal : Wasserman pour les intervalles ; OCC pour les termes/risques.
- Risques : synthétique confondu avec réel, statut supérieur à la preuve, formules orphelines.
- Validation : schémas, golden reports, inspection autonome/offline.

### Implémentation proposée

1. Ajouter `DecisionGrade` calculé et monotone.
2. Unifier les sections minimales sans casser les rapports historiques.
3. Créer matrice formule→source→code→test et audit d'intégrité CI.
4. Créer `docs/research/2026_validity_audit.md` et `errata_registry.yaml`.
5. Réconcilier `known_limits.md` et `LIMITATIONS.md` avec redirections stables.

Commit proposé : `docs(reporting): publish evidence grades formula lineage and current limits`

## Phase 10 — Validation intégrale et revue des limites

### Exécution proposée

1. Rejouer unit/property/integration/golden/offline/security.
2. Reproduire chaque expérience depuis son manifest.
3. Comparer précision/performance avant/après.
4. Auditer chaque claim et rétrograder tout statut non prouvé.
5. Produire limites, dette, données manquantes et décision de release.

Commandes minimales :

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src scripts
.venv/bin/pip check
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/security_gate.py
```

Commit proposé : `test(validation): complete quantitative evidence and safety review`

## Phase 11 — Évaluation des extensions avancées

### Documentary Research

- Questions : gain matériel de Bergomi/rough vol/filtering/taux avancés sur TTWO ; données/identifiabilité/coût.
- Principaux : tous les fragments Bergomi ; Andersen–Piterbarg ; Gatheral à obtenir.
- Secondaires : Glasserman, Tsay, Nocedal/Wright, Särkkä.
- Risques : sophistication séduisante, calibration instable, gain inobservable.
- Validation : ablation OOS, sensibilité du classement, CI du gain, coût numérique.

### Gate d'évaluation

Chaque extension reçoit l'un des statuts : `reject`, `defer`, `prototype`, `candidate_for_implementation`. Aucun modèle n'est intégré parce qu'un livre le décrit. L'implémentation exigerait une phase séparée et une nouvelle validation utilisateur.

Commit proposé si évaluation documentaire seulement : `docs(research): evaluate advanced ttwo model extensions`

## Ordre des commits et arrêt

Un commit par phase, aucune Phase N+1 si tests/gates de N échouent. La Phase 0 doit se terminer par son seul commit documentaire puis ce plan s'arrête jusqu'à validation. Aucun push, merge ou changement de branche distante n'est prévu sans demande explicite.
