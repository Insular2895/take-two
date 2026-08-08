# Handoff final français — validation quantitative TTWO, phases 0 à 11

Date : 2026-08-08  
Document canonique : [`final-quantitative-validation-handoff.md`](final-quantitative-validation-handoff.md)

## 1. Résumé exécutif

Le dépôt est terminé comme moteur de recherche quantitative en lecture seule, auditable et fermé
par défaut. Il ne constitue pas une stratégie de trading validée.

Statuts finaux :

- logiciel de recherche : `READY_RESEARCH_ONLY` ;
- promotion financière : `BLOCKED_MISSING_REAL_EVIDENCE` ;
- affirmation maximale de bout en bout : `software_tested_only` ;
- exécution : `order_capability=forbidden` ;
- intégration de modèles avancés : `NO_ADVANCED_MODEL_IMPLEMENTATION`.

Le travail centralise les unités et les mesures `P/Q`, contrôle prix et volatilité implicite,
ajoute SVI et les diagnostics de calibration, scelle le protocole expérience/holdout, sépare les
incertitudes de simulation, de modèle et de croyance, calcule des allocations en contrats entiers
avec frontière de Pareto et `NO_TRADE`, rend les décisions événementielles séquentielles et publie
un rapport de preuve fondé sur le maillon le plus faible.

## 2. Architecture finale

```text
entrées marché/preuves (provenance + heure de disponibilité)
  -> contrats quantitatifs (unités, décompte des jours, P/Q)
  -> prix / IV / SVI / diagnostics de calibration
  -> graphe de dépendance des événements + croyances bornées
  -> simulation de trajectoires + état de sortie chronologique + incertitude
  -> faisabilité en contrats entiers + objectifs robustes + frontière de Pareto
  -> grade de preuve au maillon faible + rapports statiques
  -> portes de release et d’extensions avancées
  -> sortie consultative uniquement ; cash/NO_TRADE toujours possible
```

Rôle des principaux modules :

- `quantitative/` : contrats, contrôles numériques, IV, SVI, calibration et incertitude de
  probabilité/modèle ;
- `simulation/` : machine de sortie, réduction de variance et intervalles ;
- `optimization/` : objectifs versionnés et frontière de Pareto entière exacte dans l’univers
  fini ;
- `intelligence/` : événements point-in-time, dépendances, sensibilités et intégration ;
- `validation/` : manifestes, gouvernance du holdout, audit de release et porte d’extension ;
- `reporting/` : sidecar de preuve complet et vues statiques sans réseau ;
- `docs/research/` : inventaire des livres, sources, formules, errata et recherches par phase.

## 3. Installation et validation

Installation locale :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Validation complète :

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pip check
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/validate_research_registry.py
.venv/bin/python scripts/phase10_release_audit.py --check
.venv/bin/python scripts/phase11_extension_gate.py --check
.venv/bin/python scripts/security_gate.py
```

Résultat final :

- 194 tests réussis ;
- Ruff réussi ;
- mypy strict réussi sur 144 fichiers source ;
- `pip check` réussi ;
- six schémas vérifiés ;
- artefacts offline validés en tant que fixtures uniquement ;
- 25 identifiants de formule et 36 sources reliés correctement ;
- audits déterministes des phases 10 et 11 réussis ;
- 138 fichiers Python scannés, zéro import interdit et zéro transmission activée.

Seul avertissement restant : dépréciation tierce `websockets.legacy` sous Python 3.14.

## 4. Exemples livrés

- configuration scanner : `configs/thesis_scanner/default.yaml` ;
- configuration intelligence : `configs/intelligence/v11.yaml` ;
- preuve finale synthétique : `reports/examples/phase9_final_evidence.json` ;
- exemple `NO_TRADE` : `phase9-synthetic-no-trade`, où l’absence de calibration empirique fait
  préférer le cash ;
- exemples de classement synthétique : bull call spread prudent 230/250 mars 2027, call long
  équilibré 280 mars 2027 et call long agressif 300 mars 2027 ;
- tous ces exemples restent `watchlist` et illustrent le fonctionnement déterministe, pas des
  trades retenus.

Aucun exemple réel n’a été ajouté, car aucun jeu de données aligné, autorisé, point-in-time, lié à
un manifeste et à un holdout frais n’est disponible. V7–V9 restent contaminés.

## 5. Ce qui a changé

### Fondations mathématiques

- types explicites de mesure, unité, année, session et observation ;
- transitions `P/Q` fermées par défaut ;
- facteur d’actualisation et conventions centralisés ;
- comparateur numérique absolu/relatif et audit de convergence par raffinement ;
- validation Black–Scholes contre QuantLib.

### Volatilité et calibration

- solveur IV avec bornes, résidu, itérations et échecs structurés ;
- SVI brute, ajustement déterministe, contrôles papillon/calendrier ;
- EWMA et GARCH diagnostiqués ;
- comparaison chronologique rolling/EWMA/GARCH ;
- portes Heston et eSSVI sans promotion prématurée.

### Validation expérimentale

- manifeste hashé liant code, configuration, dataset, split, essais et seed ;
- purge, embargo et suffixe hors échantillon chronologique ;
- holdout final scellé et journal d’ouverture unique ;
- PBO corrigé pour les égalités, DSR explicitement approximatif et placebo de signal valide ;
- séparation permanente des expériences contaminées V7–V9.

### Simulation et incertitude

- machine d’état chronologique des sorties ;
- contrôles de discrétisation ;
- intervalles de Wilson et taille effective ;
- variables de contrôle, antithétiques et bootstrap circulaire par blocs ;
- décomposition de l’incertitude intra-modèle, inter-modèles et Monte Carlo.

### Décision et optimisation

- objectifs d’allocation versionnés ;
- contraintes dures séparées des scores ;
- énumération exacte des contrats entiers ;
- frontière de Pareto complète ;
- cash/`NO_TRADE` toujours présent ;
- graphe de preuves événementielles, neutralisation des doublons et facteurs communs ;
- probabilités bornées selon leur origine et mises à jour chronologiques.

### Reporting et sécurité

- niveau de preuve monotone au maillon faible ;
- rapports Markdown/HTML statiques sans actifs réseau ;
- matrices source → formule → code → test ;
- registre d’errata ;
- audits de release et d’extensions reproductibles ;
- interdiction permanente de toute capacité d’ordre ou de transmission.

## 6. Livres, sources et formules

Accès français :

- [inventaire des livres](research/book_inventory.md) ;
- [sources expliquées](research/sources.fr.md) ;
- [formules et traçabilité](research/formules-et-tracabilite.fr.md) ;
- [recherche des phases 1 à 11](research/recherche-documentaire-phases-1-a-11.fr.md).

Points importants :

- les onze fichiers Bergomi forment une œuvre locale fragmentée et incomplète, pas onze livres ;
- les trois fichiers de taux reconstituent des parties des volumes I et II
  d’Andersen–Piterbarg, pas trois volumes complets ;
- Gatheral *The Volatility Surface*, Shreve II et Andersen–Piterbarg III manquent ;
- les articles primaires SVI/rough-volatility couvrent uniquement les affirmations réellement
  utilisées ;
- aucune formule issue d’un résumé seul n’a été promue.

## 7. Modèles volontairement absents

La phase 11 n’intègre aucun nouveau modèle. Sont différés : Bergomi variance forward, rough
Bergomi, filtrage bayésien, eSSVI, régimes appris, Bayes événementiel hiérarchique,
Longstaff–Schwartz et Sobol/QMC. Sont rejetés seulement dans le périmètre actuel : taux
stochastiques/HJM/LMM, Greeks supérieurs/AAD et surfaces neuronales.

Bergomi ne devient pertinent qu’après une baseline Heston/SVI validée et un gain OOS stable sur
des surfaces TTWO multi-dates. Les taux avancés ne deviennent pertinents que si leur sensibilité
change matériellement prix ou rangs par rapport à la courbe déterministe. Ces conditions ne sont
pas démontrées.

## 8. Limites et données manquantes

Dette technique restante :

- anciens noms `Bayesian*` conservés pour compatibilité ;
- checkpoints quotidiens incapables d’observer tous les franchissements intrajournaliers ;
- conformité PBO au texte intégral encore `to_review` ;
- calibrations réelles SVI/Heston et ruptures structurelles non exercées ;
- alias local du dossier de livres à confirmer ;
- avertissement de dépréciation `websockets.legacy`.

Données nécessaires avant promotion empirique :

- chaînes TTWO point-in-time sous licence avec bid/ask, OI, volume et timestamps ;
- spot, opérations sur titres, dividendes, taux et EUR/USD alignés par vintage ;
- événements revus avec heure de disponibilité et groupes de dépendance ;
- quotes combinées, fills/rejets, commissions, spreads et slippage réels ;
- identité/hash d’un holdout final intact ;
- journal de paper trading gouverné.

La prochaine amélioration utile est donc une campagne de données réelles gouvernée, suivie de
baselines simples, validation OOS chronologique, ouverture unique du holdout et paper run.

## 9. Inventaire des modifications

Le handoff des phases 0 à 11 compare la base Git
`178cfe8d3a3c3c882798775384c96570e04fda2b` à la fin de la phase 11. Il recense 69 fichiers créés
et 27 modifiés, soit 96 chemins dans ce périmètre. Le diff complet contre `main` inclut aussi les
travaux V10/V11 antérieurs présents sur la branche et atteint 311 fichiers.

Pour la liste exacte des 96 chemins du handoff, consulter la section
[Exact repository file manifest](final-quantitative-validation-handoff.md#8-exact-repository-file-manifest).
Pour tout le diff de branche, utiliser GitHub **Files changed** une fois la branche publiée, ou
localement :

```bash
git diff --stat main...HEAD
git diff main...HEAD
git log --oneline main..HEAD
```

## 10. Interprétation finale

Le dépôt démontre une discipline logicielle, numérique et documentaire solide dans son périmètre.
Il ne démontre pas encore une capacité prédictive TTWO, une rentabilité, une exécution réaliste ou
une conformité de distribution commerciale. Toute lecture doit conserver cette distinction.

