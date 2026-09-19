# Audit des valeurs codées en dur

> Mise à jour PRE-OPRA du 2026-08-30 : cet audit conserve les observations historiques, mais
> `src/take_two_options/engine.py` et `src/take_two_options/scoring.py` ont depuis été migrés puis
> supprimés. L'orchestration autoritative est `decision/pipeline.py`; le ranking actif est
> Pareto-first et les modèles non éligibles ne peuvent plus piloter une décision.

## Conclusion

Le dépôt n'a pas de strike ni d'échéance TTWO spécifique figé dans son moteur central de génération.
Les principaux risques de hardcoding sont ailleurs :

1. identité TTWO et sources datées injectées dans le pipeline/reporting générique ;
2. paramètres de modèles illustratifs utilisables comme valeurs par défaut de schéma ;
3. seuils de validation et scores heuristiques encore inscrits dans le Python ;
4. contrats d'options supposant parfois un multiplier standard de 100 ;
5. politiques dupliquées entre plusieurs YAML et quelques fallbacks Python.

Les valeurs déjà dans les YAML ne sont pas « correctement validées » du seul fait d'être
configurables. Beaucoup sont explicitement `calibration_required`, `experimental` ou
`user_assumption`. Elles doivent rester des hypothèses, jamais devenir des defaults universels.

## Méthode et règle de classement

L'audit statique a couvert les 138 fichiers Python sous `src/`, les 6 scripts, quatre arbres de
configuration, les schémas, les tests, les fixtures et les modules legacy encore importables. Les
recherches ont porté sur littéraux TTWO, dates, montants, probabilités, seuils, tailles
d'échantillon, seeds, horizons, coefficients, URLs, multipliers et valeurs par défaut.

Les catégories sont celles du brief :

- `mathematical_invariant` : identité mathématique ou convention numérique intrinsèque ;
- `software_default` : valeur technique sûre, exposée et remplaçable ;
- `configurable_policy` : choix de produit/méthode à versionner ;
- `market_data` : observation datée à charger depuis une source ;
- `user_assumption` : hypothèse explicite, jamais présentée comme fréquence observée ;
- `strategy_parameter` : définition de l'univers/recherche/sortie ;
- `validation_threshold` : gate à préenregistrer et tester ;
- `temporary_fixture_value` : exemple uniquement ;
- `incorrectly_hardcoded` : valeur métier/domaine placée dans le cœur ou silencieusement injectée.

« Code : oui » signifie que la constante peut légitimement rester dans le code. « Config : oui »
signifie qu'une analyse ordinaire doit pouvoir la changer sans modifier Python. Pour une donnée de
marché, la cible correcte est le dataset/provider, pas un fichier de politique.

## Occurrences importantes

| Fichier / symbole | Valeur actuelle | Catégorie | Justification | Code | Config | Cible | Tests requis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `domain.py:FundamentalSnapshot.validate_scenario_probabilities` | somme = 1 | `mathematical_invariant` | Une distribution doit totaliser 1 ; seule la tolérance numérique est implémentation | oui | non | aucune | somme invalide rejetée, tolérance flottante |
| `quantitative/svi.py:raw_svi_total_variance` et `quantitative/pricing.py:_normal_cdf_batch` | coefficients/formules publiées | `mathematical_invariant` | Formules mathématiques, pas décisions métier | oui | non | registre de formules | tests de référence et lineage |
| Tolérances flottantes dans SVI, probabilités, symétrie | `1e-6`, `1e-8`, `1e-10`, `1e-12` | `software_default` | Garde numérique locale ; externaliser aveuglément nuirait à la stabilité | oui | non, sauf tolérance de convergence utilisateur | `numerical_policy` seulement si matériel | tests limites/scale et non-régression |
| `domain.py:PricingConfiguration` | grids `100/100`, bornes `25..1000` | `software_default` | Discrétisation technique déjà exposée dans un objet | oui | oui | `model_universe.pricing_numerics` | convergence multi-grid et coût/temps |
| `domain.py:MarketDataBundle` | paths `512`, seed `42` | `software_default` | Paramètres de calcul/reproductibilité, pas faits de marché | fallback technique oui | oui | `validation_policy.monte_carlo` | reproductibilité et convergence avec plusieurs path counts |
| `domain.py:MarketDataBundle` | horizon `120`, vol `0.35`, dividende `0` | `user_assumption` | Paramètres économiques qui ne doivent pas être silencieux | non comme hypothèses universelles | oui | `model_universe`, `market_context`, `scenario_set` | absence de valeur → blocage ou provenance |
| `domain.py:JumpDiffusionParameters` | intensité `0.8`, moyenne `-0.08`, vol `0.16` | `user_assumption` | Paramètres illustratifs, pas calibration TTWO | schéma peut accepter, pas fournir silencieusement | oui | `model_universe.models[].parameters` avec origin/status | statut illustratif, impossible à promouvoir sans calibration |
| `domain.py:HestonParameters` | `2.0`, `0.1225`, `0.65`, `-0.6`, `0.1225` | `user_assumption` | Paramètres Heston non calibrés ; des defaults peuvent être confondus avec un fit | non comme valeurs implicites | oui | `model_universe.heston` | missing/illustrative bloqué ; gate identifiabilité |
| `configs/intelligence/v11.yaml:simulation.heston` | `0.1225, 2.0, 0.1225, 0.45, -0.55` | `user_assumption` | Correctement étiqueté `illustrative`, mais à exclure des conclusions réelles | non | oui | même cible, `origin=illustrative` obligatoire | manifest conserve origine ; rapport affiche blocage |
| `configs/intelligence/v11.yaml:local_volatility_nodes` | neuf nœuds 0–1 an | `temporary_fixture_value` | Surface illustrative, non observée | non | oui uniquement profil fixture | `fixtures/` ou `scenario_set.synthetic_surface` | fixture incapable de produire statut calibrated |
| `domain.py:PortfolioState.research_share_quantity` | `10` actions | `strategy_parameter` | Quantité de baseline/portefeuille, pas constante universelle | non | oui | `capital_constraints.baselines.underlying_quantity` | budget/currency et quantité entière |
| `knowledge/schemas.py:TradeRequest.safety_reserve_fraction` | `0.05` | `configurable_policy` | Réserve de capital ; déjà surchargeable mais default silencieux | validation de borne seulement | oui | `capital_constraints.safety_reserve_fraction` | 0, borne haute, impact allocation |
| `knowledge/schemas.py:DataRefreshPolicy` | strike limit `40`, cache fallback `true` | `configurable_policy` | Coût/complétude de collecte ; déjà dans YAML trade | valeur technique de secours seulement | oui | `market_context.data_refresh` | changement sans Python, pagination/couverture |
| `knowledge/schemas.py:MaintenancePreferences` | revue `7` jours, rolling/recovery/scale-out `true` | `strategy_parameter` | Règle de gestion, pas défaut universel | non | oui | `strategy_universe.maintenance` | chaque préférence désactivable |
| `candidate_generation/search_space.py:build_search_space` | fallback DTE `1..horizon` | `incorrectly_hardcoded` | Une recette incomplète s'élargit silencieusement | non | oui ou fail-closed | `strategy_universe.recipes[].dte` | recette incomplète bloquée ; diagnostics explicites |
| même symbole | fallback moneyness `0.01..10` | `incorrectly_hardcoded` | Bande quasi universelle cachée, contraire au contrat data/config-driven | non | oui ou fail-closed | `strategy_universe.recipes[].moneyness` | aucune génération hors bande déclarée |
| `candidate_generation/search_space.py:_range_values` | minimum/midpoint/maximum | `configurable_policy` | Densité de recherche implicite à trois points | algorithme oui | oui | `optimization_objective.search_sampling` | nombre/grille configurables et manifestés |
| `candidate_generation/enumerator.py:_valid_width` | tolérance `1e-8` | `software_default` | Comparaison flottante locale | oui | non | aucune | largeurs proches/éloignées |
| `candidate_generation/enumerator.py` calendrier | front minimum = holding min + `7` jours | `strategy_parameter` | Buffer opérationnel matériel si la recette ne le fournit pas | non | oui | `strategy_universe.recipes[].front_dte_buffer_days` | calendriers avec/sans buffer |
| `decision/pipeline.py:_historical_path` | fallback fichiers `ttwo_*` | `incorrectly_hardcoded` | Le chemin générique retombe sur une identité TTWO | non | non ; résolution par manifeste | `market_context.dataset_id` | XYZ ne touche aucun fichier TTWO |
| `decision/pipeline.py:_sources` | `take-two-q2-fy2026`, URL/date, ECB 2026-07-17 | `incorrectly_hardcoded` | Sources spécifiques injectées dans toute décision, même autre ticker/date | non | métadonnées via registry/dataset | `research_request.source_ids`, source registry | source absente non injectée ; XYZ propre |
| `decision/pipeline.py:_progressive_final_evaluation` | convergence max(`5 %`, `5 USD`) | `validation_threshold` | Critère matériel de fin de simulation | non | oui | `validation_policy.monte_carlo_convergence` | scale currency, sensibilité, non-convergence |
| `decision/pipeline.py` | cinq finalistes/diagnostics | `configurable_policy` | Limite de reporting/recherche, pas invariant | non | oui | `report_policy.max_candidates` | 1/N/tous et ordre stable |
| `reporting/evidence_grade.py:FinalDecisionEvidenceReport` | ticker `Literal["TTWO"]` | `incorrectly_hardcoded` | Bloque directement la portabilité du reporting | non | donnée requête | `research_request.ticker` | rapport XYZ JSON/MD/HTML |
| `reporting/evidence_grade.py` titres | « TTWO final... » | `incorrectly_hardcoded` | Présentation générique figée au symbole | non | template dérivé de la requête | `report_policy.title_template` | escaping et titre XYZ |
| `intelligence/schemas.py:NormalizedEvidenceEvent/EventNormalizationRule` | entity `TTWO` | `incorrectly_hardcoded` | Le module événement peut être TTWO, pas le contrat universel | non | oui | `research_request.entity` ou config domaine TTWO | entité obligatoire, événements XYZ isolés |
| `market_snapshot.py:load_latest_market_snapshot` | deux chemins legacy TTWO datés | `incorrectly_hardcoded` | Compatibilité historique acceptable temporairement, mais non générique | couche legacy seulement | résolution par manifeste | migration vers catalogue dataset | fallback marqué legacy ; XYZ indépendant |
| `thesis_scanner/enumeration.py:_quote_reasons` | multiplier doit être `100` | `validation_threshold` | Politique prudente pour standard contracts, mais le multiplier doit venir du contrat et les ajustés être explicitement compris | règle oui | oui | `strategy_universe.contract_policy` | 100 accepté, inconnu bloqué, ajusté compris traité selon policy |
| `intelligence/backtesting.py:WalkForwardCase.multiplier` | défaut `100` | `incorrectly_hardcoded` | Un backtest ne doit pas inventer le deliverable/multiplier | non | dataset, pas config | champ obligatoire du contrat historique | absence bloquée ; multiplier non standard valorisé exactement |
| `intelligence/backtesting.py:WalkForwardDataset.embargo_days` | `5` | `validation_threshold` | Embargo dépend du label/horizon | non | oui | `validation_policy.embargo` | 0/N, purge, overlap |
| `intelligence/backtesting.py:_execute/_metrics` | perte totale `95 %`, VaR/CVaR `95 %` | `validation_threshold` | Définitions de risque à versionner ; le brief exige aussi 10/25/50/70/90/near-total | code calcul générique oui | oui | `risk_profile.loss_thresholds`, `report_policy.risk_levels` | monotonie ladder, base capital, seuil exact |
| `intelligence/backtesting.py:_ece` | `10` bins | `validation_threshold` | ECE est sensible au binning | algorithme oui | oui | `validation_policy.probability_metrics.ece_bins` | bins alternatifs, faible N |
| `quantitative/calibration.py:fit_ewma` | decay grid `0.85,0.90,0.94,0.97` | `strategy_parameter` | Espace de calibration préenregistré, pas invariant | oui pour mécanique | oui | `model_universe.ewma.decay_candidates` | registry d'essais et meilleure valeur déterministe |
| `quantitative/calibration.py:fit_garch_11` | alpha/beta grids, persistance `<0.995`, alertes `0.98/0.10` | `validation_threshold` | Contraintes/stabilité doivent être versionnées et sensibles | oui pour stationnarité | oui pour grille/alertes | `model_universe.garch`, `validation_policy.calibration` | stationnarité, limites, grid hash |
| `quantitative/calibration.py:compare_volatility_forecasts` | train `100`, test `20`, fenêtre `40` | `validation_threshold` | Taille de preuve et benchmark | non | oui | `validation_policy.sample_sizes`, `model_universe.historical_window` | juste sous/au-dessus du seuil |
| `quantitative/calibration.py:evaluate_heston_calibration_gate` | `20` dates, `4` maturités, `5` strikes | `validation_threshold` | Gate prudent mais à justifier et versionner | règle oui | oui | `validation_policy.heston_gate` | toutes frontières et combinaisons insuffisantes |
| `quantitative/svi.py:svi_arbitrage_report` | grille `[-3,3]`, `601` points | `software_default` | Diagnostic numérique, à manifester ; pas une hypothèse de marché | oui | oui pour validation exhaustive | `model_universe.svi.arbitrage_grid` | violation entre grilles, convergence |
| `quantitative/svi.py:fit_svi_slice/evaluate_essvi_gate` | min 5 quotes, 4 échéances | `validation_threshold` | Couverture minimale requise | oui | oui | `validation_policy.surface_gate` | 4/5 quotes, 3/4 échéances, arbitrage |
| `intelligence/calibration.py:build_dataset_splits` | embargo `5`, train `60`, val/test/holdout `20` | `validation_threshold` | Duplicata d'une politique déjà présente ailleurs | non | oui, source unique | `validation_policy.splits` | contrat unifié, aucune divergence entre moteurs |
| `intelligence/calibration.py:fit_offline_models` | 30 closes, 3 dates/5 strikes, 3-sigma/5 jumps | `validation_threshold` | Gates empiriques et classification jump | non | oui | `validation_policy.calibration`, `model_universe.jump` | seuils frontières, statut insuffisant |
| `intelligence/data_hub.py:UnifiedDataHub` | fraîcheur 24h/24h/1h/7j/30j/120j/14j | `configurable_policy` | Bons fallbacks techniques, mais domaine/décision dépendants | fallback oui | oui | `market_context.freshness` | chaque domaine, stale/future/missing |
| `configs/trades/ttwo_gta6_1000eur.yaml` | ticker, dates, budget 1000 EUR, max loss 1000, horizon, catalyst | `user_assumption` | Correct emplacement projet, pas recommandation | non | oui | `research_request`, `capital_constraints`, `risk_profile` | surcharge complète sans Python |
| même config | OI 20, spread 30 %, coûts 0.65/0.05, max 4 contrats | `validation_threshold` | Préenregistré mais `calibration_required`/compte à confirmer | non | oui | `execution_assumptions`, `validation_policy`, `capital_constraints` | limites, provenance, coût zéro interdit en validation réelle |
| même config | EUR/USD `1.1435` au 2026-07-17 | `market_data` | Observation datée, pas valeur durable de politique | non | dataset/provider | `market_context.fx_series` | fraîcheur, available-at, source et conversion inverse |
| `configs/thesis_scanner/default.yaml` | taux `4 %`, dividende `0`, FX `1.1435` | `market_data` | Valeurs datées ou à vérifier, actuellement décrites comme inputs | non | dataset/provider | `market_context.rates/dividends/fx` | stale/missing bloque usage actuel |
| même config | moneyness `0.70..1.70`, widths, LEAPS 365, IV multipliers, spot grid | `strategy_parameter` | Univers de recherche/scénarios | non | oui | `strategy_universe`, `scenario_set` | nouvelle grille sans Python, hash manifest |
| même config `profile_weights` | trois vecteurs de poids | `configurable_policy` | Classement heuristique explicite, mais non calibré | non | oui | `optimization_objective.secondary_ranking` | sommes, sensibilité, corrélations, aucune promotion primaire |
| `configs/research/default.yaml:ranking_policy` | poids 0.25/0.20/.../0.05 | `configurable_policy` | Déjà secondaire et expérimental ; meilleur emplacement que Python | non | oui | `optimization_objective.secondary_ranking` | somme/clefs, permutation, sensibilité |
| `decision/ranking.py` liquidité | OI / (OI + `100`) | `incorrectly_hardcoded` | Échelle de saturation non documentée, influence le ranking | non | oui ou calibration empirique | `optimization_objective.normalization.liquidity` | scale OI, missing, sensibilité |
| `scoring.py:score_candidate` (supprimé le 2026-08-30) | nombreux 0.70/0.80/0.90, coefficients 2/4/30, moyenne égale | `incorrectly_hardcoded` | Le score legacy opaque/non versionné a été retiré après migration de ses consommateurs | non | non | historique uniquement | test d'absence du module et du second pipeline |
| `thesis_scanner/ranking.py:_criteria` | missing liquidity 0.35, mix 0.50/0.35/0.15, theta 2 %, préférences 1/0.65/0.45 | `incorrectly_hardcoded` | Heuristiques Python en plus des poids YAML | non | oui | `optimization_objective.profile_normalization` | missingness, monotonicité, ablation, sensibilité |
| `intelligence/covariance.py` | poids récence 0.45/0.35/0.20, event 0.25, régime 0.30 | `configurable_policy` | Pondération modèle non présente dans `V11Policy` | non | oui | `model_universe.covariance.weighting` | poids N fenêtres, somme, stabilité PSD |
| `intelligence/valuation.py:summarize_robustness` | score 0.65/0.20/0.15, gates 0.5/0.8/0.25 | `incorrectly_hardcoded` | Composite et verdict influencés par coefficients non versionnés | non | oui | `validation_policy.robustness` ; futur `model_agreement` distinct | monotonie, ablation, score version, désaccord extrême |
| `intelligence/valuation.py:_empirical_metrics` | convergence 10 %, quantiles 5/95 | `validation_threshold` | Niveaux d'incertitude et convergence à versionner | calcul générique oui | oui | `validation_policy.uncertainty` | couverture, petit N, convergence |
| `intelligence/valuation.py:_empirical_metrics` | coefficient `1.96` | `mathematical_invariant` | Quantile normal approximatif de l'IC bilatéral 95 %, valide seulement sous l'approximation déclarée | oui | niveau de confiance oui | `validation_policy.uncertainty.confidence_level` | référence normale et alternative petit échantillon |
| `intelligence/event_normalization.py` | multipliers qualité par source, ex. live 0.95/delayed 0.65 | `configurable_policy` | Hiérarchie de preuve, pas vérité mathématique | non | oui | `validation_policy.evidence_quality` | ordre monotone, source inconnue, version |
| `validation/placebo.py` | alpha `0.05` | `validation_threshold` | Niveau statistique préenregistré | non | oui | `validation_policy.significance_alpha` | alpha alternatifs, puissance insuffisante |
| `validation/legacy_vetoes.py` | spread max `35 %` | `incorrectly_hardcoded` | Duplique/contredit potentiellement les politiques YAML | legacy isolé seulement | oui | `execution_assumptions.liquidity` | même résultat entre moteur actif/legacy ou dépréciation claire |
| URLs API MarketData/Alpaca/SEC/FRED | endpoints officiels stables | `software_default` | Invariants d'adapter, remplaçables par injection/base URL pour test | oui | base URL optionnelle | config provider/environnement | mock transport, aucune clé dans URL/log |
| `alpaca_data.py` disponibilité options historiques | début `2024-02-01` | `validation_threshold` | Limite dépendant du provider et susceptible d'évoluer | fallback documenté seulement | oui/métadonnée provider | `market_context.providers[].capabilities` | borne avant/après et mise à jour source |
| Seeds datés dans YAML/fixtures | `20260725`, `20260728`, etc. | `software_default` | Reproductibilité d'un run, sans signification économique | oui comme entrée manifestée | oui | `validation_policy.seed` | replay exact et seeds alternatifs |
| Toutes valeurs sous `fixtures/` et rapports exemples | prix, dates, probabilités synthétiques | `temporary_fixture_value` | Elles testent la mécanique et portent un statut fixture/synthetic | oui dans fixtures | non pour production | `fixtures/` uniquement | aucun chemin fixture ne peut promouvoir evidence/holdout |
| `order_capability`, `transmit`, `what_if`, human confirmation | `forbidden`, `False`, `True`, `True` | `software_default` | Invariants de sécurité volontairement non configurables | oui | non | aucune | scan statique, adapter order-capable rejeté, stubs lèvent |

## Valeurs à conserver dans le code

Les éléments suivants ne doivent pas être externalisés par réflexe :

- identités de payoff et formules publiées ;
- somme des probabilités égale à 1 ;
- bornes logiques Pydantic (`probabilité ∈ [0,1]`, quantités entières positives) ;
- constantes de conversion purement dimensionnelles et petites tolérances numériques locales ;
- `transmit=False`, `what_if=True`, `order_capability=forbidden` et confirmation humaine ;
- ask pour un achat et bid pour une vente dans le scénario prudent, tant qu'une autre convention
  explicite ne remplace pas ce scénario.

## Priorité de correction

### P0 — Phase B

- supprimer `Literal["TTWO"]`, titres et sources TTWO du cœur générique ;
- rendre multiplier/deliverable obligatoires dans les observations de backtest ;
- unifier les contrats de configuration et retirer les fallbacks business silencieux ;
- créer la preuve de portabilité `XYZ` ;
- conserver tous les paramètres illustratifs avec origine/statut explicites.

### P1 — Phases C à G

- déplacer taux/FX/dividendes vers données datées ;
- unifier tailles d'échantillon, purge/embargo, convergence et gates modèle ;
- manifester les grilles de calibration et l'espace d'essais ;
- versionner coût, risque et comparabilité des baselines.

### P1 — Phases J et K

- remplacer les heuristiques Python par des méthodologies justifiées/versionnées ou les maintenir
  uniquement comme ranking legacy secondaire ;
- créer cinq scores indépendants, loss ladder et payoff severity sans réutiliser le
  `robustness_score` comme substitut ;
- tester sensibilité et double comptage avant toute classification.

## Sources et limites

- Sources : dépôt local, configurations, tests, rapports, manifests et mémoire projet du vault.
- Source externe nouvelle : aucune.
- Limite : l'audit recense les valeurs **matériellement pertinentes** pour les résultats, la
  portabilité, la validation et la sécurité. Il ne transforme pas chaque entier de boucle, code
  HTTP, longueur de hash ou constante de format en paramètre métier.
- Aucun seuil identifié ici n'est validé comme décision finale. Les seuils marqués
  `calibration_required`, `experimental`, `draft_to_validate` ou `user_assumption` restent à
  valider.
