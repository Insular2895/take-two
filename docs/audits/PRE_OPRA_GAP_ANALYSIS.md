# Audit pré-OPRA — analyse des écarts

## Décision immédiate

La Phase A est terminée au niveau de l'audit. Le dépôt est un moteur de recherche
**lecture seule, correctement testé sur ses invariants logiciels**, mais il n'est pas encore un
moteur de décision pré-OPRA validé empiriquement.

Le statut conservateur exact est :

- release logicielle : `READY_RESEARCH_ONLY` ;
- niveau de preuve maximal : `software_tested_only` ;
- verdict financier pré-OPRA : `BLOCKED_BY_DATA` ;
- supériorité de V10 face aux baselines : **non mesurée** ;
- calibration TTWO réelle complète : **non démontrée** ;
- holdout final vierge : **non créé et non ouvert** ;
- capacité d'ordre : `forbidden`.

`BLOCKED_BY_DATA` décrit ici l'état du programme de validation, pas une recommandation de
position. Aucun chiffre de performance, aucune calibration et aucun résultat de holdout n'a été
inventé pendant cet audit.

## Périmètre et point de départ

| Élément | Valeur auditée |
| --- | --- |
| Date de l'audit | 2026-08-08 |
| Branche | `codex/v10-quantitative-validation-and-robust-decision-engine` |
| Commit de départ | `62b438d0e813230f0530f3dabc90238e47cf8fd4` |
| Remote | `origin` → `https://github.com/Insular2895/take-two.git` |
| Périmètre exécuté | Phase A uniquement |
| Phase M | non démarrée |
| Ordres broker | interdits par contrat, scan statique et stubs qui lèvent une erreur |

L'audit a couvert le README, les 138 fichiers Python sous `src/`, les 35 modules `test_*.py` et
`tests/conftest.py`, les
configurations, schémas, données locales, fixtures, rapports, registres de recherche, validations,
intégrations de données et frontières broker. Les sources longues n'ont pas été retraitées : leurs
extractions, errata et filiations déjà enregistrés ont d'abord été vérifiés.

## Résultats de contrôle de l'état initial

Les commandes canoniques du dépôt ont été exécutées dans `.venv` :

| Contrôle | Résultat |
| --- | --- |
| `.venv/bin/python -m pytest -q` | `194 passed`, 1 avertissement de dépréciation tiers |
| `.venv/bin/ruff check .` | succès |
| `.venv/bin/mypy src scripts` | succès sur 144 fichiers (`src` + scripts) |
| `.venv/bin/pip check` | aucune dépendance cassée |

Un appel initial avec les exécutables système a échoué parce que le package et ses dépendances de
développement ne sont pas installés globalement. Ce n'est pas un défaut du dépôt : le README et la
CI prescrivent explicitement `.venv`.

## État réel des données observées

Le dépôt Git ne versionne aucun fichier sous `data/`. Toutefois, le poste contient un cache local
ignoré par Git dans `data/marketdata/cache/` :

- 1 998 réponses historiques MarketData.app ;
- 46 413 lignes d'options TTWO ;
- 250 dates de requête du 2025-07-21 au 2026-07-23 ;
- appels et puts ;
- 82 strikes distincts observés entre 75 et 390 USD ;
- 65 échéances observées entre le 2025-07-25 et le 2028-01-21 ;
- bid, ask, volume, open interest, sous-jacent et timestamps présents dans les réponses inspectées ;
- IV et Greeks nuls sur ces 46 413 lignes ;
- hash de payload et date de récupération présents au niveau du cache.

Ces fichiers constituent une matière première utile pour la Phase C, mais **pas encore un dataset
de validation autorisé** : ils sont ignorés par Git, ne possèdent pas de manifeste de dataset
global, n'explicitent pas leur licence dans un contrat de dataset, ne sont pas alignés avec toutes
les séries requises et n'ont pas encore fait l'objet d'un audit complet de disponibilité
point-in-time. Les rapports Alpaca et MarketData déjà présents prouvent des parcours réels de
collecte et des calculs de recherche, pas une comparaison holdout reproductible.

Les fixtures sous `fixtures/` sont correctement marquées synthétiques ou exemples. Elles ne doivent
jamais être promues en preuve TTWO réelle.

## Matrice d'écarts complète

Les statuts ont le sens imposé par le brief : `already_complete`, `partial`, `missing`,
`blocked_by_data`, `requires_opra` et `requires_other_external_data`.

### Architecture, configuration et portabilité

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| Contrat de configuration versionné et unifié | `partial` | `TradeRequest`, `ThesisScanPolicy`, `V11Policy` et trois familles YAML sont strictement validés | Les 11 groupes requis sont fragmentés ; `target_return`, `risk_profile`, `model_universe`, `optimization_objective` et `report_policy` ne forment pas un seul contrat. Phase B. |
| Ticker, budget, devise et perte maximale configurables | `already_complete` | `TradeRequest` et `configs/trades/ttwo_gta6_1000eur.yaml`; tests de budget/perte | À raccorder au contrat unifié sans réécrire les contrôles existants. Phase B. |
| Objectif, préférence de risque, scénarios et modèles modifiables sans Python | `partial` | Profils, scénarios et modèles existent dans les YAML V10/V11 | Les conventions et objectifs restent répartis, et certains fallbacks sont dans les schémas Python. Phase B. |
| Strikes et échéances issus de la chaîne disponible | `already_complete` | `candidate_generation` énumère les strikes/échéances de `MarketSnapshot`; tests d'énumération et de structures calendaires | Conserver. Ajouter seulement la preuve `XYZ` en Phase B. |
| Registre de stratégies génériques | `already_complete` | Recettes YAML bornées et catalogue compilé couvrant 15 architectures ; quantités entières et relations entre jambes testées | Conserver les recettes, ne pas réécrire le registre. |
| Portabilité du cœur sur `XYZ` | `missing` | Plusieurs contrats acceptent un ticker libre | Aucun fixture/test `XYZ`; `FinalDecisionEvidenceReport.ticker` est `Literal["TTWO"]`, les titres de rapports sont figés TTWO, certains chemins/sources ont des fallbacks TTWO. Phase B. |
| README « generic » conforme à l'implémentation | `partial` | La génération et la majorité des contrats sont génériques | La promesse de la ligne 6 est trop large tant que reporting, événements V11 et fallbacks ne sont pas séparés et qu'un test `XYZ` ne passe pas. Phase B. |

### Dataset, provenance et intégrité temporelle

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| Dataset historique TTWO complet et gouverné | `blocked_by_data` | Adapters Alpaca/MarketData, caches locaux réels et normalisation OCC existent | Aucun dataset versionné/manifesté, aligné et juridiquement qualifié ne permet aujourd'hui les Stages 1–6. Audit licence et construction en Phase C. |
| Droits de conservation/réutilisation du cache local | `requires_other_external_data` | Le cache porte endpoint, récupération, hash et payload, mais pas un champ de licence exploitable | Les conditions du provider et les droits du compte doivent être confirmés avant d'intégrer ou publier le dataset. Phase C. |
| Sous-jacent OHLCV, ajustements et corporate actions | `partial` | Collecteur Alpaca et schémas existent ; rapport de calibration réel historique présent | Pas de bundle immuable aligné avec les chaînes, ni politique ajusté/non-ajusté validée. Phase C. |
| Options historiques avec identité, bid/ask, OI, volume et timestamps | `partial` | Cache local : 46 413 lignes avec ces champs principaux ; parseur OCC et contrôles de quote testés | IV/Greeks absents, complétude et licences non auditées, données non gouvernées. Phase C. |
| Rates, dividendes, FX, calendrier et corporate actions alignés | `blocked_by_data` | Treasury, FRED, ECB configuré, calendrier et contrats de provenance existent | Séries vintages/available-at alignées absentes du dataset final. Phase C. |
| États `observed/derived/imputed/missing/unavailable_from_source` | `partial` | Qualité, source, hash et erreurs sont exposés dans V11 | Les cinq états demandés ne sont pas unifiés au niveau de chaque observation du dataset historique. Phase C. |
| Manifeste avec dataset ID/version/provider/timestamps/hash/licence/PIT/qualité | `partial` | `HistoricalDataset`, `UnifiedObservation`, `SourceProvenance` et manifests de snapshots couvrent une grande partie | Contrat final consolidé et manifeste réel absents. Phase C. |
| Priorité des sources et traitement des contradictions | `partial` | Registre de sources et clusters de contradictions existent | `docs/data/SOURCE_PRIORITY.md` manque, ainsi qu'une règle globale de résolution sans écrasement. Phase C. |
| Intégrité point-in-time et anti-look-ahead | `partial` | `available_at <= decision_time`, cutoff, contrat disponible, expiration/strike disponibles et rejets post-cutoff sont testés | Il faut appliquer ces invariants à toutes les séries réelles et auditer OI/EOD, publications, FX et révisions. Phases C/E/I. |
| Dataset événementiel TTWO point-in-time | `partial` | Schémas, règles, déduplication, contradictions et connecteurs SEC/RSS existent ; fixtures testées | Pas de corpus réel revu ni d'étude historique des réactions spot/IV/skew/spread. Phase I. |

### Calibration et modèles

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| Statistiques empiriques (retours, RV, skew, kurtosis, gaps, drawdowns, bootstrap) | `partial` | Retours log, volatilité, intervalles, bootstrap et tail risk existent dans plusieurs modules | Pas de rapport unique calculé sur dataset TTWO gouverné ; skew/kurtosis/gaps et stabilité restent à consolider. Phase D. |
| EWMA et GARCH(1,1) gaussien | `partial` | Implémentations déterministes, fail-closed et tests synthétiques | Pas de calibration TTWO gouvernée ni d'erreurs standards, AIC/BIC, Ljung-Box et couverture VaR complets. Phase D. |
| GJR-GARCH/EGARCH et innovations Student-t | `missing` | Aucun modèle actif correspondant | À n'ajouter en Phase D que comme comparateurs mesurables, avec critères préenregistrés. |
| SVI/eSSVI et arbitrage | `partial` | Fit raw-SVI, diagnostics butterfly/calendrier et gate eSSVI testés sur synthétique | Historique réel de surfaces et stabilité de paramètres absents. Phases D/H. |
| Heston calibré uniquement si identifiable | `partial` | Gate explicite 20 dates/4 maturités/5 strikes et statut insuffisant ; aucun faux paramètre promu | Les valeurs illustratives V11 existent encore pour la simulation ; calibration réelle correctement bloquée. Phases D/H. |
| Absence d'ajout de modèles de prestige | `already_complete` | Revue Phase 11 rejette/diffère rough vol, Bergomi, filtres latents et taux stochastiques | Maintenir ce gate. |
| Validation et statut de chaque modèle | `partial` | Seeds, positivité, convergence, arbitrage local-vol et statuts sont testés | Mesures réelles OOS, stabilité, erreurs de calibration et pouvoir prédictif manquent. Phases D/E/H. |

### Walk-forward, holdout, baselines et preuve de valeur

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| Walk-forward rolling/expanding | `partial` | Contrats et évaluateur existent ; prix prudents et splits séparés sont testés | Le rapport ne journalise pas encore toutes les bornes, paramètres, prédictions et hashes sur un dataset réel. Phase E. |
| Purge et embargo | `partial` | Primitives et tests de frontières/embargo existent | Leur application à un panel TTWO réel complet n'est pas prouvée. Phase E. |
| Manifeste d'expérience reproductible | `partial` | Hash code/config/data/split/trials/seed testé | Aucun manifeste d'expérience actif et rejouable n'est enregistré. Phase E. |
| Holdout final réellement frais | `blocked_by_data` | Contrat de ledger hash-chaîné, accès unique et blocage du retuning testés en mémoire | `validation/final_holdout_ledger.jsonl` manque ; aucun ID/hash de dataset neuf ne peut être scellé honnêtement. Phase F. |
| États irréversibles du holdout | `partial` | `seal/evaluate/report/tune` et chaîne de hash existent | Les états demandés `UNOPENED/OPENED_ONCE/CONTAMINATED/INVALID` et la persistance JSONL doivent devenir le contrat public. Phase F. |
| Baselines obligatoires | `partial` | Enum et moteur : cash, underlying, ATM, fixed-delta, spread, random, oracle, modèle et NO_TRADE ; tests de présence/prix prudents | Le rapport committé contient `baselines_present: []`; buy-and-hold et comparabilité complète restent à produire sur données réelles. Phase G. |
| Table de comparaison V10/baselines | `missing` | Aucun tableau final calculé conforme | À générer uniquement avec observations compatibles. Phase G/L. |
| Deltas explicites face aux baselines | `missing` | Seul regret en USD est prévu | Uplifts rendement/CVaR/DD/probabilités/Sharpe/Sortino/coûts manquent. Phase G. |
| Contrôles de multiple testing | `partial` | DSR, PBO, placebo, purged CV et registre append-only existent/testés | Espace de recherche effectif, FDR/permutation si appropriés et verdict intégré manquent. Phase G. |
| Significativité versus matérialité économique | `partial` | Intervalles et statistiques de recherche existent | Aucune règle/version de verdict ni comparaison coût-net réelle. Phase G. |
| Verdict de valeur du moteur | `missing` | Les statuts fail-closed généraux existent | Aucun calcul ne répond encore aux questions « V10 améliore quoi ? ». Phase G/L. |

### Qualité de décision et diagnostics de risque

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| `opportunity_score` 0–100 | `missing` | Un score explicatif secondaire min-max existe | Ce score n'est ni le score demandé ni une preuve ; méthodologie, version et sensibilité manquent. Phase J. |
| `risk_score` 0–100 | `missing` | Des métriques de risque brutes existent | Aucun score indépendant conforme. Phase J. |
| `evidence_score` 0–100 | `missing` | Un grade weakest-link discret existe | Le grade de preuve ne remplace pas le score quantitatif demandé. Phase J. |
| `model_agreement_score` 0–100 | `missing` | Dispersion multi-modèles et `robustness_score` existent | Formule d'accord, normalisation et rangs inter-modèles manquent. Phase J. |
| `execution_quality_score` 0–100 | `missing` | Spreads/OI/volume/fraîcheur/coûts par jambe existent | Score autonome et limitations historiques documentées manquent. Phase J. |
| Métriques brutes affichées avec chaque score | `missing` | Les objets bruts existent dans différents rapports | Aucun contrat d'affichage score → métriques explicatives. Phase J/L. |
| Pas de score magique primaire | `partial` | Pareto/vetos précèdent le ranking secondaire configurable | Le score legacy moyen et certains scores V10/V11 ont des coefficients codés en Python ; il faut les isoler/versionner. Phase B/J. |
| Classifications finales configurables | `missing` | `NO_TRADE`, posture et grades existent | Les neuf labels et leurs règles versionnées ne sont pas implémentés. Phase J. |
| `NO_POSITION_RECOMMENDED` au niveau portefeuille | `partial` | Cash/NO_TRADE est une solution admissible et testée | Nom, contrat final et affichage systématique des candidats/distance aux contraintes manquent. Phases J/K. |
| Meilleur candidat bloqué | `partial` | Jusqu'à cinq diagnostics bloqués et raisons de veto sont conservés | Les cinq scores et distances numériques aux contraintes ne sont pas calculés. Phase K. |
| Échelle de pertes sévères 10/25/50/70/90/near-total | `missing` | 50 %, 70 % et perte quasi totale apparaissent dans des générations différentes | Une seule échelle cohérente et systématique manque. Phase K. |
| `payoff_severity` mesurable | `missing` | Convexité, theta, breakeven et pertes totales existent séparément | Agrégation/version/interprétation absentes. Phase K. |
| Fréquence de no-position et attribution | `partial` | `no_trade_rate` global existe | Ventilation année/régime/budget/objectif/qualité et raisons standardisées absentes. Phase K. |
| Sensibilité des gates et `GATE_INSTABILITY` | `partial` | Des artefacts de sensibilité et tests de stabilité paramétrique existent | Balayage préenregistré seuil → fréquence/retour/CVaR/DD/pertes sévères non intégré. Phase K. |
| Frontière opportunité/risque | `missing` | Pareto générique existe | Les axes scores et encodages evidence/execution/agreement manquent. Phases J/K/L. |
| Front de Pareto | `already_complete` | Allocation exacte, cash préservé, dominance testée et documentée | Étendre ses dimensions après création des scores ; ne pas réécrire l'algorithme. Phase K. |
| Validation des règles de sortie | `partial` | Profit/stop/time/expiry, trajectoires et coûts sont modélisés | Avec EOD, l'ordre intraday n'est pas connaissable ; les trois conventions optimistic/conservative/worst-case ne sont pas comparées systématiquement. Phase G/K. |

### Documentation, exécution, OPRA et reporting

| Exigence | Statut | Fonctionnement et preuve actuels | Écart exact / phase cible |
| --- | --- | --- | --- |
| BOOK, multi-PDF et provenance documentaire | `partial` | Inventaire de 138 chemins/137 PDF, hashes, regroupements et extractions bornées | Le chemin `BOOK` reste un alias candidat vers `/Users/insular/Desktop/book 📙` à confirmer ; 61 avertissements qpdf sont tracés. Aucune réécriture requise. |
| Summarizer / Transcript | `partial` | Syntaxe et workflows sont documentés ; recherches des Phases 1–11 tracées | « Transcript » correspond probablement au pipeline Summarizer mais cette équivalence reste à valider. |
| Registre de sources | `already_complete` | 36 entrées auditées par le release review | Continuer à l'alimenter uniquement avec sources réellement utilisées. |
| Registre de formules et traçabilité code/tests | `already_complete` | 25 formules, matrice de lineage et validation de registre | Ajouter les futures formules des scores en Phases J/K. |
| Errata et validité 2026 | `already_complete` | Registres dédiés présents et validés | Mettre à jour uniquement si nouvelles sources/modèles. |
| Dépendances logicielles | `already_complete` | Versions bornées dans `pyproject.toml`, `pip check` et CI | La dépréciation `websockets.legacy` est tierce et non bloquante actuellement. |
| Modèle de coûts d'exécution | `partial` | Ask/bid prudents, commissions/slippage configurés et tests | Hypothèses compte/broker non calibrées ; fill, impact, combo et rejets réels absents. Phases C/G et futur M. |
| Scénarios d'exécution | `partial` | bid/ask x2, slippage x2, frais x2, midpoint unavailable et liquidation prudente existent | Plusieurs sorties sont proxies ou `data_insufficient`; scénarios versionnés et comparables manquent. Phase K. |
| Document de périmètre pré-OPRA | `missing` | Limites dispersées dans README/READINESS/known_limits | `docs/validation/PRE_OPRA_SCOPE.md` manque. Phase L. |
| Frontière OPRA | `already_complete` | Port IBKR market-data-only, adapter non connecté, preview `transmit=False`, scan global testé | Conserver strictement. |
| Abstraction `LiveOptionMarketDataProvider` | `partial` | `DataConnector` et `IBKRDataPort` séparent déjà collecte et broker | Une interface générique commune historique/live avec capacités explicites reste à formaliser. Phase B/L. |
| Plan final de validation OPRA | `partial` | `IBKR_OPRA_ROADMAP.md` couvre une partie du futur | `docs/validation/OPRA_FINAL_VALIDATION_PLAN.md`, critères promotion, durée, incidents et rollback manquent. Phase L, exécution en M seulement. |
| Framework paper trading | `partial` | Dossier position, replay, monitoring, décision humaine et guide paper existent | Registre immuable décision/quote/fill/rejet/slippage/latence et critères de campagne manquent. Phase L ; campagne en M. |
| Broker what-if futur | `requires_opra` | Port combo quote et emplacement `what_if_results` existent | Nécessite session broker autorisée, conIds et compte ; ne pas exécuter avant M. |
| Validation prospective OPRA | `requires_opra` | Limites et readiness reconnaissent le blocage | Stage 7 / Phase M uniquement. |
| Aucune exécution automatique | `already_complete` | Stubs interdits, imports order bloqués, scan AST et tests | Invariant à préserver dans chaque phase. |
| Dashboard final multidimensionnel | `partial` | JSON/Markdown/HTML statique et visualisations riches existent | Les cinq scores, échelle de pertes, baseline table, best blocked et verdict moteur manquent. Phase L. |
| Plusieurs candidats visibles | `already_complete` | Classements, Pareto, candidats diagnostics et rapports exhaustifs existent | Adapter au nouveau contrat de scores sans masquer les rejetés. Phase L. |
| Rapport final pré-OPRA | `missing` | Rapports partiels V10/V11 et exemple evidence grade existent | Le contrat complet de la section 67 et ses artefacts JSON/MD/HTML manquent. Phase L. |
| Reproductibilité finale | `partial` | Seeds, manifests, hashes, essais et cache déterministe existent | Versions de scores, dataset réel, environnement et manifeste actif rejouable manquent. Phases B–L. |
| Tests spécifiques du brief | `partial` | 194 tests prouvent beaucoup d'invariants et la sécurité | Manquent `XYZ`, score monotonicity/sensitivity, severe-loss ladder, persistent holdout, baselines réelles, final report et gate stability. Phases B–L. |
| Versionnement des scores dans le run manifest | `missing` | Le manifest contient versions modèles/policy | `score_versions` et hashes de formules absents. Phase J. |

## Divergences documentation / implémentation

1. Le README affirme un moteur « generic ». La génération principale l'est largement, mais le
   rapport final impose `TTWO`, ses titres HTML/Markdown sont figés et aucun test `XYZ` n'existe.
2. `docs/BACKTESTING.md` dit que le holdout est verrouillé et jamais utilisé pour tuning. Le contrat
   impose bien `final_holdout_used_for_tuning=False`, mais cela ne prouve pas un holdout réel : le
   release audit confirme qu'il n'a jamais été créé.
3. Le README décrit les baselines obligatoires avec justesse, mais l'artefact V11 committé indique
   qu'aucune baseline n'est présente. La fonctionnalité est donc testée mécaniquement, pas validée
   empiriquement.
4. Les rapports historiques Alpaca/MarketData montrent de la donnée réelle et des calculs, tandis
   que le release audit affirme correctement qu'aucun dataset autorisé aligné n'est **committé**.
   Les deux affirmations sont compatibles, mais le futur rapport devra distinguer clairement cache
   local, dataset gouverné et preuve holdout.

## Plan d'implémentation exact — Phases B à L

Ce plan est une proposition d'exécution technique. Les seuils, formules de score, objectifs et
critères de promotion restent `draft_to_validate` jusqu'à validation explicite. Chaque phase doit
produire un commit atomique et laisser `order_capability=forbidden`.

### Phase B — Nettoyage config/data-driven et preuve de portabilité

1. Créer `src/take_two_options/config/contracts.py` avec un `PreOpraResearchConfigV1` strict
   contenant exactement les 11 groupes du brief.
2. Ajouter `configs/pre_opra/v1/default.yaml` sans transformer les valeurs d'exemple du brief en
   recommandations ; chaque hypothèse doit porter `value`, `origin`, `as_of` et `status` si elle
   n'est pas observée.
3. Ajouter un loader unique, un export JSON Schema et les hashes config/policy dans le run manifest.
4. Adapter les anciens YAML via une couche de compatibilité, sans supprimer les contrats stables.
5. Retirer du cœur les sources et titres TTWO codés en dur ; garder GTA/TTWO dans un module/config
   de domaine.
6. Faire échouer explicitement les recettes incomplètes au lieu d'utiliser des bornes silencieuses
   `0.01/10`, et rendre la densité de recherche configurable.
7. Créer `fixtures/portability/xyz_option_chain.json` et
   `tests/test_portability_xyz.py` couvrant pricing, génération, risque, optimisation, validation et
   reporting sans modification du Python.
8. Exit criteria : schéma versionné, compatibilité anciennes configs, aucun ticker/budget/objectif/
   seuil important à modifier dans Python, test XYZ vert, tests existants verts.

### Phase C — Dataset historique TTWO point-in-time

1. Créer un contrat de dataset sous `src/take_two_options/datasets/` et un manifeste immuable sous
   `datasets/manifests/` ; ne pas committer une donnée dont la licence l'interdit.
2. Auditer le cache local MarketData : intégrité des hashes, doublons, couverture, trous,
   timestamps, droits de conservation/redistribution et sémantique EOD.
3. Collecter/aligner, depuis les sources déjà autorisées, sous-jacent, actions corporate,
   dividendes, chaînes options, Treasury/rates, EUR/USD et calendrier.
4. Matérialiser pour chaque observation l'état provenance demandé et les cinq temps pertinents.
5. Créer `docs/data/SOURCE_PRIORITY.md`, un catalogue de contradictions et les règles de
   résolution sans écrasement.
6. Réserver un intervalle futur au holdout sans exposer ses observations ; aucun tuning ne doit
   l'utiliser.
7. Tests : schema/property, hashes, licence obligatoire, anti-look-ahead par domaine, corporate
   actions, quote crossing, disponibilité du contrat, absence d'imputation critique silencieuse.
8. Exit criteria : dataset ID/hash, manifeste, couverture chiffrée, limites et missingness ; sinon
   statut `BLOCKED_BY_DATA` conservé.

### Phase D — Calibration empirique réelle

1. Produire statistiques descriptives et distributions bootstrap sur la partie train uniquement.
2. Consolider historical variance/EWMA/GARCH(1,1), puis implémenter GJR ou EGARCH et Student-t
   seulement comme comparateurs préenregistrés.
3. Ajouter erreurs standards, log-vraisemblance, AIC/BIC, Ljung-Box, diagnostics résiduels,
   stabilité, forecast RV et couverture VaR.
4. Calibrer SVI/eSSVI uniquement sur slices admissibles ; journaliser erreurs, arbitrage,
   interpolation/extrapolation et stabilité.
5. Appliquer le gate Heston avant tout fit ; si la couverture ou l'identifiabilité échoue, émettre
   exactement `BLOCKED_INSUFFICIENT_CALIBRATION_DATA` et exclure les paramètres illustratifs de
   toute conclusion empirique.
6. Tests : récupération sur synthétique, fail-closed, non-look-ahead, stabilité numérique,
   comparaisons de likelihood, sérialisation des diagnostics.
7. Exit criteria : un rapport par modèle avec statut réel et hashes ; aucun modèle ajouté pour
   prestige.

### Phase E — Walk-forward avec purge et embargo

1. Raccorder les splits existants au dataset C et à la calibration D.
2. Enregistrer par fenêtre toutes les bornes, hashes, paramètres gelés, prédictions, contrats
   disponibles, résultats et coûts.
3. Exécuter rolling et expanding ; purger le chevauchement des labels et appliquer l'embargo
   configuré.
4. Interdire toute recalibration avec observation future et toute lecture du holdout.
5. Émettre un `ExperimentManifest` actif, un registre d'essais exhaustif et un replay déterministe.
6. Tests : zéro overlap, embargo, contrat first-seen, données révisées, échec si timestamp naïf ou
   manifeste non reproductible.
7. Exit criteria : résultats OOS non-holdout par fenêtre ou blocage chiffré pour insuffisance.

### Phase F — Holdout final vierge et ledger persistant

1. Formaliser `UNOPENED`, `OPENED_ONCE`, `CONTAMINATED`, `INVALID` et les transitions
   irréversibles.
2. Ajouter un store JSONL append-only utilisant la chaîne de hash déjà testée et le chemin exact
   `validation/final_holdout_ledger.jsonl`.
3. Sceller ID/hash/période/config avant toute ouverture. Un fichier vide peut représenter
   `UNOPENED`; aucune fausse entrée d'accès ne sera créée sans dataset.
4. Exiger acteur, motif, commit, config hash, résultat hash et timestamp pour l'unique évaluation.
5. Rejeter tuning, sélection de feature/modèle/stratégie/seuil/score/coût après ouverture.
6. Tests : corruption de chaîne, deuxième ouverture, tuning, changement de dataset/config,
   crash/reprise et concurrence.
7. Exit criteria : ledger persistant vérifiable ; s'il n'existe pas de dataset neuf, statut
   `UNOPENED`/`BLOCKED_BY_DATA`, jamais une validation fictive.

### Phase G — Baselines, comparabilité et multiple testing

1. Construire les baselines depuis le même snapshot disponible : cash/no position, actions TTWO,
   buy-and-hold si comparable, call ATM, call delta fixe, bull call spread standard et candidat
   admissible aléatoire ; garder l'oracle non exploitable.
2. Partager horizon, capital, FX, multiplier, frais, spreads et conventions d'entrée/sortie.
3. Calculer la table complète et tous les deltas du brief avec intervalles et coûts.
4. Mesurer l'espace effectif de recherche et appliquer DSR, PBO, purged CV, placebo/permutation et
   correction multiple appropriée, sans tuning holdout.
5. Séparer significativité statistique, matérialité économique et incertitude.
6. Valider les sorties EOD sous scénarios optimistic/conservative/worst-case quand l'ordre intraday
   est inconnu.
7. Tests : égalité des conventions, déterminisme random baseline, oracle exclu des gates,
   coûts non nuls, petit uplift classé inconclusif.
8. Exit criteria : verdict préliminaire `ENGINE_ADDS_VALUE`, `ENGINE_NOT_PROVEN_SUPERIOR`,
   `PROMISING_BUT_NOT_PROVEN`, `BLOCKED_BY_DATA` ou `VALIDATION_FAILED`, strictement dérivé.

### Phase H — Validation historique des surfaces options

1. Reconstruire chaque surface admissible à partir du dataset C.
2. Calculer IV localement, total variance, raw-SVI puis eSSVI si ses gates passent.
3. Enregistrer ATM vol, skew, courbure, terme, paramètres, erreurs, arbitrage, flags
   interpolation/extrapolation et couverture de quote.
4. Étudier stabilité, ruptures et comportement événementiel sans utiliser le holdout.
5. Tests : slices insuffisantes bloquées, arbitrage détecté, calendrier monotone, identités
   contractuelles, replay exact.
6. Exit criteria : série historique auditable ou blocage par couverture/licence ; Heston reste
   bloqué si l'identifiabilité ne passe pas.

### Phase I — Dataset événements/régimes et réactions

1. Construire le dataset événementiel réel avec `published_at`, `available_at`, qualité source,
   duplicate cluster et contradiction status.
2. Réviser humainement les événements texte matériels avant toute influence probabiliste.
3. Aligner fenêtres de réaction spot/RV/IV/skew/volume/spread et séries macro.
4. Définir les régimes avec règles préenregistrées et distinguer corrélation, inférence et
   causalité non prouvée.
5. Tests : disponibilité après clôture, doublons, contradictions, source dependency, post-cutoff,
   événement non revu neutralisé.
6. Exit criteria : couverture et incertitude publiées ; likelihoods restent `user_assumption` ou
   `configured_heuristic` tant qu'elles ne sont pas calibrées OOS.

### Phase J — Cinq scores indépendants et classifications

1. Définir d'abord les métriques brutes, unités, sens, échantillon requis et traitement du manque.
2. Étudier scaling, distributions, corrélations et double comptage sur train/validation seulement.
3. Créer cinq contrats/version : opportunity, risk, evidence, model agreement et execution quality.
4. Documenter dans `docs/methodology/` les formules, normalisations, poids justifiés, intervalles,
   limites et sensibilité ; inscrire chaque formule au registre.
5. Ajouter `score_versions` et hashes au run manifest. Garder le ranking composite secondaire,
   configurable et explicitement non décisionnel.
6. Implémenter les neuf classifications par règles configurables et `NO_POSITION_RECOMMENDED` au
   niveau portefeuille.
7. Tests : bornes 0–100, monotonies attendues, missing data, invariance d'unités, no magic score,
   score élevé incapable de masquer une métrique brute ou un veto, sensibilité des poids.
8. Exit criteria : aucun poids arbitraire promu ; si l'étude ne justifie pas une formule, le score
   reste `BLOCKED_INSUFFICIENT_DATA`.

### Phase K — Pertes sévères, sévérité et sensibilité des gates

1. Calculer sur les mêmes paths/observations les six probabilités de perte, avec intervalles et
   base de capital explicite.
2. Définir/versionner `payoff_severity` à partir de propriétés mesurables, sans label intuitif.
3. Calculer les distances signées à chaque contrainte et publier le meilleur candidat bloqué.
4. Mesurer no-position global et par année/régime/budget/objectif/qualité avec raisons normalisées.
5. Exécuter une grille de seuils modeste, fixée avant les résultats, et émettre `GATE_INSTABILITY`
   selon une règle validée.
6. Étendre le Pareto existant et construire la frontière opportunity/risk sans fusionner les axes.
7. Tests : monotonie de l'échelle de pertes, cas near-binary, distances, grilles non adaptatives,
   Pareto/dominance et invariance de l'ordre.
8. Exit criteria : diagnostics présents même pour `NO_POSITION_RECOMMENDED` et candidats extrêmes.

### Phase L — Dashboard et rapport final pré-OPRA

1. Créer `docs/validation/PRE_OPRA_SCOPE.md` et
   `docs/validation/OPRA_FINAL_VALIDATION_PLAN.md`.
2. Formaliser l'interface live générique, le schéma immuable du journal paper et les critères de
   promotion futurs, sans connecter OPRA ni envoyer d'ordre.
3. Créer un contrat de rapport final JSON et les rendus Markdown/HTML réseau-free avec : données,
   modèles, walk-forward, holdout, cinq scores + métriques brutes, baselines, deltas, pertes,
   sensibilité, no-position, best blocked, verdict, limites et readiness OPRA.
4. Ajouter la table multi-candidats et les visualisations opportunity/risk, Pareto, gate
   sensitivity et baseline deltas.
5. Mettre à jour README, known limits, source/formula registries, errata, schémas et readiness pour
   refléter exactement les statuts calculés.
6. Exécuter pytest/ruff/mypy/pip check, validateurs de schémas/artefacts/registres, release audit,
   security gate et CI complète.
7. Exit criteria : documentation = implémentation, rapport rejouable, verdict dérivé, limitations
   visibles, `order_capability=forbidden`. La Phase M reste explicitement future.

## Ordre critique et règles de non-contamination

- La politique de holdout et l'intervalle réservé doivent être figés avant la sélection empirique
  des modèles, même si la persistance finale du ledger est livrée en Phase F.
- Les Phases D, E, G, H, I, J et K n'utilisent que train/validation/test autorisés.
- La première ouverture du holdout vient après gel du code, des scores, des seuils, des coûts et du
  registre d'essais ; elle n'autorise aucun retuning.
- Un échec face à une baseline est publié, pas corrigé après observation du holdout.
- Une phase bloquée par la licence, la couverture ou la donnée doit rester bloquée ; elle ne doit
  jamais être remplacée par une fixture pour produire un résultat favorable.

## Sources utilisées pour cet audit

- Dépôt local : code, configurations, tests, caches ignorés, rapports, manifests et documentation.
- Mémoire locale : règles et note projet TTWO du vault Graphipy Maxi Brain.
- Corpus documentaire déjà enregistré : `docs/research/source_registry.yaml`,
  `formula_registry.yaml`, `formula_lineage_matrix.md`, `errata_registry.yaml` et
  `2026_validity_audit.md`.
- Sources externes nouvelles : aucune. Aucune vérification web ni connexion OPRA n'était nécessaire
  pour constater l'état de la Phase A.
