# Recherche documentaire des phases 1 à 11 — synthèse française

Date : 2026-08-08  
Statut global : `recherche_sourcée_et_implémentée_sans_promotion_empirique`  
Documents canoniques : `phase-1-documentary-research.md` à
`phase-11-documentary-research.md`

## Principe commun

Chaque phase commence par une question précise, inspecte des passages ciblés, sépare les faits des
hypothèses, compare les alternatives, implémente uniquement ce que les preuves autorisent et
conserve les limites. Les PDF locaux sont restés en lecture seule. Une extraction automatique ou
un résumé n’a jamais été traité comme une preuve quantitative autonome.

## Phase 1 — conventions, mesures et audit numérique

### Ce qui a été retenu

- Les dynamiques empiriques sous `P` doivent être séparées de la valorisation sans arbitrage sous
  `Q`. Toute transition de mesure doit être explicite et sourcée.
- Le temps calendaire d’une option et l’échantillonnage des rendements ne sont pas la même
  convention : Actual/365 Fixed est utilisé pour l’échéance, 252 séances seulement pour
  annualiser des observations empiriques.
- Une comparaison numérique doit publier erreur absolue, erreur relative, tolérances et statut.
- Une seule grille fine ne prouve pas la convergence : il faut une suite de raffinements.

### Sources et traduction en code

Björk, Andersen–Piterbarg et Süli–Mayers ont fondé les contrats `P/Q`, le facteur d’actualisation,
les conventions temporelles et le rapport de convergence. Les chaînes libres ambiguës et les
égalités exactes entre flottants ont été rejetées au profit de types et diagnostics explicites.

### Limites

Les anciens schémas sérialisés ne sont pas tous réécrits. La comparaison QuantLib couvre surtout
le cas européen. Cette phase ne crée aucune preuve prédictive ou holdout.

## Phase 2 — volatilité implicite diagnostiquée et surface SVI

### Ce qui a été retenu

- La volatilité implicite est la racine de `prix_modèle(vol)-prix_cible`.
- La bissection est la base robuste lorsqu’un intervalle de signe valide existe ; elle doit
  exposer bornes, prix aux bornes, itérations, résidu, tolérances et échec éventuel.
- SVI paramètre la variance implicite totale, pas directement la volatilité.
- Une tranche SVI ajustée n’est pas automatiquement sans arbitrage : il faut contrôler le
  papillon `g(k)>=0` et la non-décroissance calendaire de variance totale.
- eSSVI est différé tant que plusieurs échéances point-in-time suffisamment denses ne permettent
  pas de mesurer un gain.

### Sources et traduction en code

Süli–Mayers justifie la bissection ; Gatheral–Jacquier fournit SVI et les conditions d’arbitrage ;
Cohort et al. et Mingone cadrent SSVI/eSSVI. Le solveur retourne un résultat structuré. Le fit SVI
utilise une recherche multi-départs déterministe et des moindres carrés pondérés. Le fallback
silencieux de volatilité `0.45` a été supprimé : une IV manquante échoue désormais fermée.

### Limites

Validation sur paramètres synthétiques, contrôle d’arbitrage sur grille finie, IV américaine
dépendante du modèle et eSSVI non implémenté.

## Phase 3 — calibration robuste et séries temporelles

### Ce qui a été retenu

- La volatilité est latente et conditionnelle ; volatilité réalisée et implicite ne sont pas
  interchangeables.
- GARCH(1,1) suit `h_t=ω+αε_(t-1)²+βh_(t-1)` avec coefficients positifs et persistance
  stationnaire inférieure à un.
- Après calibration, il faut examiner les résidus standardisés et leurs carrés ; la vraisemblance
  seule ne suffit pas.
- Les comparaisons rolling, EWMA et GARCH doivent produire la prévision avant d’observer le
  prochain rendement carré et être jugées chronologiquement par MSE de variance et QLIKE.
- Un Heston natif ne justifie pas une calibration depuis une seule clôture ou surface.

### Sources et traduction en code

Tsay fonde EWMA/GARCH et Bergomi la porte Heston. Les calibrations utilisent des grilles
contraintes et reproductibles avec diagnostics. Heston reste derrière une porte exigeant dates,
échéances, strikes, provenance point-in-time et multi-départs contraints.

### Limites

Le GARCH gaussien ne traite ni queues lourdes ni levier. Les diagnostics de lag sont des écrans,
pas des tests Ljung–Box complets. Aucun modèle n’est promu sans panel TTWO réel hors échantillon.

## Phase 4 — backtests point-in-time et holdout

### Ce qui a été retenu

- Un résultat de backtest est indissociable du code, de la configuration, des données, du split,
  du registre d’essais et de la seed.
- Les variables doivent être disponibles avant la décision ; purge et embargo empêchent le
  chevauchement des labels ; le holdout final reste caché jusqu’à une ouverture unique journalisée.
- Le PBO/CSCV mesure le risque de sélection parmi plusieurs stratégies ; les égalités utilisent
  désormais des rangs moyens et la moyenne des gagnants ex æquo.
- Le DSR corrige partiellement essais multiples et non-normalité mais ne remplace pas un holdout.
- Permuter les rendements et comparer leur moyenne est invalide : le placebo permute les signaux
  relativement aux rendements et calcule une p-value.

### Sources et traduction en code

Bailey et al., Bailey–López de Prado, Wasserman et la documentation FRED/ALFRED fondent le
protocole. `ExperimentManifest` lie les entrées par hash. Le journal de holdout est chaîné et
interdit tout tuning après évaluation.

### Limites

Aucun jeu de données réel n’est présent. Le protocole reste `awaiting_authorized_dataset`. V7–V9
sont contaminés et ne pourront jamais devenir le nouveau holdout final.

## Phase 5 — sorties de chemin et incertitude Monte Carlo

### Ce qui a été retenu

- Une règle de sortie est un temps d’arrêt fondé uniquement sur l’information disponible à chaque
  checkpoint. L’état complet est enregistré et toute transition non chronologique est rejetée.
- Une variable de contrôle suit `Y-b(X-E[X])`, avec `b=Cov(X,Y)/Var(X)` au minimum de variance.
- Les antithétiques sont moyennés par paire ; le nombre de réplications indépendantes est le
  nombre de paires.
- Zéro événement rare observé ne signifie pas risque nul : les probabilités non pondérées publient
  intervalle de Wilson, taille effective et seuil minimum de chemins.
- Une série dépendante utilise un bootstrap circulaire par blocs, pas un bootstrap iid ordinaire.

### Sources et traduction en code

Glasserman, Andersen–Piterbarg, Künsch et Clément–Lamberton–Protter ont été inspectés. La machine
`ExitMachineState` est immuable et sérialisable. Les rapports conservent variance avant/après,
erreur standard et facteur de réduction. Longstaff–Schwartz est différé faute d’écart matériel
mesuré contre le moteur différences finies/checkpoints.

### Limites

Des checkpoints quotidiens manquent les franchissements intrajournaliers. Les intervalles ont des
hypothèses spécifiques. L’ESS n’est pas une preuve d’indépendance. Aucun échantillonnage
d’importance d’événements rares n’est intégré.

## Phase 6 — sémantique des croyances et incertitude de modèle

### Ce qui a été retenu

- Un posterior dépend d’un jeu de données, d’une vraisemblance et d’un prior déclarés ; sa
  cohérence interne ne garantit pas sa performance réelle.
- La prédiction postérieure doit moyenner les résultats sur l’incertitude paramétrique.
- Les scores hors échantillon répondent à une question prédictive, pas à la vérité ou à la causalité.
- L’objet historique `BayesianScenarioDistribution` est en réalité une croyance heuristique
  configurée. Son étiquette active devient `configured_heuristic_belief` et sa « confiance » une
  suffisance de preuve.
- Variance prédictive interne, variance entre modèles et erreur Monte Carlo restent séparées.

### Sources et traduction en code

McElreath, Brier et Wasserman cadrent la sémantique. L’API explicite
`update_heuristic_scenario_beliefs` conserve un wrapper compatible. Chaque jeu de chemins reçoit
un SHA-256 des paramètres. Le rapport de mélange et les diagnostics Brier/log-loss/ECE sont typés.

### Limites

Les poids égaux ne sont pas une moyenne bayésienne de modèles. Aucun likelihood génératif ne relie
encore les preuves GTA VI aux scénarios. Aucun posterior ou étalonnage TTWO réel n’a été produit.

## Phase 7 — objectifs entiers et frontière de Pareto

### Ce qui a été retenu

- Les contrats d’options entiers rendent l’ensemble d’allocation discret et non convexe.
- Une relaxation continue est un diagnostic, pas un certificat d’exécution entière.
- La dominance de Pareto est calculée directement sur toutes les allocations réalisables ; la
  scalarisation ne sert qu’au classement et peut manquer des points non convexes.
- `cash/NO_TRADE` est toujours une allocation réalisable.
- Des poids de régimes heuristiques ne peuvent être étiquetés validés hors échantillon sans hash
  de preuve.

### Sources et traduction en code

Boyd–Vandenberghe fournit l’optimalité de Pareto. `OptimizationObjectiveContract` versionne les
objectifs et pénalités. L’énumération exhaustive reste l’oracle pour l’univers borné actuel et
retourne la frontière complète en plus des sélections classées.

### Limites

La frontière dépend des objectifs et candidats déclarés. Les rendements et CVaR héritent de
modèles non calibrés. Une position de Pareto n’est pas une recommandation.

## Phase 8 — scénarios d’événements et décisions séquentielles

### Ce qui a été retenu

- Une mise à jour séquentielle n’équivaut à une mise à jour jointe que sous les bonnes hypothèses
  conditionnelles.
- Les nouvelles répétées ou dérivées d’un même fait n’ajoutent aucune nouveauté ; un facteur
  commun doit recevoir une décote déclarée.
- Association et intervention causale sont distinctes ; un DAG est une hypothèse causale explicite.
- Un filtre latent demande transition, vraisemblance d’observation et séquence identifiées ; ces
  éléments manquent pour les événements TTWO.
- Croyances utilisateur, estimations historiques, probabilités calibrées et quantités implicites
  de marché gardent des origines et mesures distinctes.

### Sources et traduction en code

Blitzstein–Hwang, McElreath et Särkkä ont été inspectés. Un graphe de preuves acyclique et
point-in-time porte relations et décotes. Les boîtes de probabilités sont propagées par extrêmes
exacts sur le simplexe. Les règles restent consultatives, peuvent retourner `NO_TRADE` et gardent
`order_capability=forbidden`.

### Limites

Aucune probabilité, distribution de choc ou décote de dépendance TTWO n’est calibrée. Les
intervalles marginaux ne sont pas des régions de confiance simultanées. Le seuil de croyance garde
les P&L conditionnels fixes.

## Phase 9 — reporting, niveaux de preuve et risques des options

### Ce qui a été retenu

- Un point estimé doit avoir un intervalle fini ou un diagnostic d’indisponibilité.
- L’origine de tout intervalle de probabilité doit être visible ; une sensibilité heuristique
  n’est pas une couverture de confiance.
- Le niveau de preuve est une chaîne monotone : proposé, implémenté, testé, validé numériquement,
  validé empiriquement, holdout, puis paper trading.
- Le niveau global est le minimum des composants requis.
- Les risques OCC — prime entièrement perdable, liquidité, exercice, perturbation de marché — ne
  peuvent être effacés par un rang favorable.

### Sources et traduction en code

Wasserman, Glasserman et l’ODD officiel OCC ont été inspectés. Un sidecar final typé, des rendus
Markdown/HTML statiques, une matrice de traçabilité, un registre d’errata et un validateur CI ont
été ajoutés.

### Limites

Les hashes prouvent l’identité, pas la qualité des données. Les intervalles dépendent de leurs
hypothèses. Le tableau de bord est une vue de preuve, pas un conseil financier personnalisé.

## Phase 10 — validation intégrale et audit des affirmations

### Ce qui a été retenu

- La validation est une échelle : le bon fonctionnement mécanique n’établit pas l’exactitude
  prédictive.
- La reproductibilité exige un manifeste actif liant code, configuration, dataset, split, essais
  et seed.
- L’absence de manifeste réel est un blocage, pas une permission de transformer une fixture en
  donnée réelle.
- La release utilise le maillon de preuve le plus faible et conserve l’exécution interdite.

### Résultat

Le statut final est `READY_RESEARCH_ONLY`. La promotion financière est
`BLOCKED_MISSING_REAL_EVIDENCE` et l’affirmation maximale de bout en bout est
`software_tested_only`. Aucun manifeste réel n’a été rejoué, aucun holdout final n’a été ouvert et
V7–V9 restent contaminés.

### Limites

Il manque données d’options point-in-time sous licence, holdout propre, paper run, observations de
fills/slippage et revue externe. La comparaison de temps n’est qu’un smoke test sur une exécution.

## Phase 11 — matérialité des extensions avancées

### Résultat immédiat

Aucune extension étudiée ne démontre une valeur décisionnelle incrémentale pour TTWO : huit sont
`defer`, trois sont `reject` uniquement dans le périmètre actuel, zéro est `prototype` et zéro est
`candidate_for_implementation`.

| Extension | Statut actuel | Condition minimale de réouverture |
| --- | --- | --- |
| Bergomi variance forward | différé | gain OOS stable contre Heston/SVI |
| Rough Bergomi | différé | rugosité TTWO stable et gain OOS |
| Filtrage bayésien | différé | modèle préenregistré et meilleure calibration OOS |
| Taux stochastiques/HJM/LMM | rejet périmètre actuel | variation matérielle de prix/rang contre courbe déterministe |
| eSSVI | différé | échec mesuré de SVI puis gain de stabilité réel |
| Régimes appris | différé | gain chronologique OOS contre règles transparentes |
| Bayes événementiel hiérarchique | différé | population comparable et prédictions calibrées |
| Longstaff–Schwartz | différé | écart FD/checkpoints matériel et validation base/chemins |
| Greeks supérieurs/AAD | rejet périmètre actuel | sensibilité stable liée à une règle validée |
| Sobol/QMC/Monte Carlo distribué | différé | goulet profilé et gain erreur/coût reproductible |
| Surface neuronale | rejet périmètre actuel | victoire OOS avec contraintes d’arbitrage exécutables |

### Sources et décision

Bergomi, Andersen–Piterbarg, Särkkä, les articles rough-volatility et les sources déjà inspectées
ont servi à définir les portes. L’inférence est que la complexité ajouterait aujourd’hui plus de
non-identifiabilité que de preuve. Ce n’est pas un jugement théorique permanent.

Décision de phase : aucun modèle avancé intégré, toutes les portes échouent fermées, exécution
interdite et nouvelle phase revue obligatoire même si une extension devient candidate.

## Conclusion transversale

Les livres et articles ont renforcé le moteur sur trois plans : exactitude des contrats
mathématiques, traçabilité des preuves et refus des affirmations prématurées. Ils n’ont pas fourni
de preuve qu’une stratégie TTWO est rentable. La prochaine avancée utile est une campagne de
données réelles gouvernée, puis calibration de baselines, comparaison OOS chronologique, ouverture
unique d’un holdout final et paper trading — pas l’ajout immédiat d’un modèle plus sophistiqué.

