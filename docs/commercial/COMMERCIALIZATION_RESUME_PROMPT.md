# Future Phase N — resume prompt

Status: `DORMANT_PROMPT_NOT_EXECUTABLE_TODAY`

Created: 2026-08-08

Use this prompt only after Phase M, shadow mode, prospective paper validation, and final project
validation are genuinely complete. At the time this file was created, `FINAL_PROJECT_VALIDATION.md`
did not exist, the verdict was `ENGINE_NOT_PROVEN_SUPERIOR`, and Phase N was forbidden.

The text below is intended to be copied into a future Codex session.

---

Tu reprends le dépôt GitHub `https://github.com/Insular2895/take-two` pour évaluer la future
Phase N — Commercial Productization.

La Phase N n'est pas automatiquement autorisée par ce prompt. Ton premier travail est de prouver
que ses conditions d'entrée sont satisfaites. Ne commence aucune implémentation commerciale avant
un `GO` documenté et une validation explicite de l'utilisateur.

## 1. Règles absolues

Tant que les gates ci-dessous ne sont pas satisfaits, ne pas :

- créer ou modifier un SaaS, une application publique, un frontend commercial ou une API
  commerciale ;
- ajouter utilisateurs, organisations, authentification, abonnements, Stripe ou autre billing ;
- modifier le moteur quantitatif pour des raisons commerciales ;
- hard-coder des prix ou choisir un segment/tier ;
- exposer des données OPRA, broker, historiques ou tierces sans droits explicites ;
- publier le code, les paramètres, la calibration, les secrets ou le dataset propriétaire ;
- ajouter une capacité d'ordre, d'exercice ou de roll ;
- relâcher le holdout, les baselines, les scores, le risque ou le protocole scientifique ;
- confondre backtest, walk-forward, holdout, paper et live ;
- affirmer un edge, une rentabilité garantie ou une conformité juridique sans preuve actuelle.

Les invariants read-only restent :

```text
transmit=false
what_if=true
order_capability=forbidden
```

## 2. Lecture obligatoire avant toute action

Lire intégralement, dans cet ordre :

1. les instructions `AGENTS.md` applicables et les règles du vault local ;
2. `FINAL_PROJECT_VALIDATION.md` ;
3. `docs/commercial/COMMERCIALIZATION_FUTURE_PLAN.md` ;
4. ce fichier `docs/commercial/COMMERCIALIZATION_RESUME_PROMPT.md` ;
5. `docs/FINAL_PRE_OPRA_VALIDATION.md` ;
6. `docs/READINESS.md` ;
7. `docs/LIMITATIONS.md` ;
8. `docs/validation/OPRA_FINAL_VALIDATION_PLAN.md` ;
9. les rapports Phase M, shadow, paper, holdout et baselines cités par la validation finale ;
10. les manifestes de code, config, données, modèles, scores et décisions paper.

Ne jamais inventer un fichier ou une preuve absente. Si `FINAL_PROJECT_VALIDATION.md` n'existe pas,
est vide, est non reproductible, ou ne contient pas suffisamment de preuves prospectives :

```text
PHASE_N_ENTRY_GATE=CLOSED
```

Dans ce cas, expliquer les blockers et arrêter sans modifier le dépôt.

## 3. Audit d'entrée obligatoire

Vérifier et sourcer explicitement :

- Phase M OPRA terminée avec droits et entitlements autorisés ;
- shadow mode et paper trading prospectifs terminés ;
- taille d'échantillon et durée conformes au protocole préenregistré ;
- décisions gelées avant réalisations et chaîne de hashes valide ;
- probabilités, Brier, ECE, intervalles et calibration validés ;
- cinq scores, couverture, monotonie et seuils validés ;
- severe-loss ladder, CVaR, drawdown et risque calibrés ;
- spreads, frais, slippage, rejects et trous de données observés ;
- comparaison V10 contre les mêmes baselines sur les mêmes timestamps et coûts ;
- stabilité par régime et tests de sensibilité ;
- holdout utilisé au maximum une fois selon sa gouvernance, sans retuning ultérieur ;
- revue indépendante, provenance et reproductibilité du verdict final.

Un pari gagnant, un x3, un scénario GTA réussi ou quelques trades positifs ne satisfont pas cet
audit.

Produire une table `preuve / source / date / statut / limite / blocker` et séparer :

- faits vérifiés ;
- hypothèses ;
- inférences ;
- contraintes externes ;
- décisions utilisateur validées ;
- décisions encore à valider.

## 4. Routage selon le verdict quantitatif final

Appliquer sans réinterprétation opportuniste :

- `VALIDATION_FAILED` : Phase N interdite ; produire `NO_GO` et arrêter.
- `ENGINE_NOT_PROVEN_SUPERIOR` : aucune revendication d'edge ; évaluer au maximum une plateforme
  research/analytics sans supériorité revendiquée, si les autres gates permettent l'étude.
- `PROMISING_BUT_NOT_PROVEN` : continuer la validation ; aucune construction commerciale.
- `ENGINE_ADDS_VALUE` : autoriser seulement l'étude N0–N4 si les preuves prospectives sont
  suffisantes. Ne pas en déduire un `GO` commercial.

Rechercher activement bugs, biais de sélection, look-ahead, contamination, multiple testing,
sur-ajustement, coûts manquants et claims excessifs avant d'accepter le verdict.

## 5. Actualisation externe obligatoire

La réglementation, les licences, les produits concurrents, les tarifs et les offres fournisseurs
sont temporellement instables. Utiliser la date réelle de la reprise et effectuer une recherche
actualisée.

Utiliser prioritairement des sources officielles ou primaires. Croiser les sources importantes.
Conserver URL, titre, date de publication ou de consultation et affirmation soutenue. Ne jamais
transformer une source en décision sans validation.

Actualiser au minimum :

- règles OPRA/exchanges et conditions du provider retenu ;
- display, non-display, derived data, storage, redistribution et commercial use ;
- cadre réglementaire de la juridiction de lancement ;
- obligations privacy, record retention, marketing et suitability ;
- options analytics SaaS, scanners, volatility tools, research platforms et API concurrentes ;
- prix, fonctionnalités, segments, droits de données, forces et faiblesses des concurrents ;
- coûts data, cloud, support, billing, monitoring, juridique et compliance.

Une analyse juridique ancienne ou un ancien tarif ne doit pas être réutilisé sans vérification.
Demander une revue juridique professionnelle ; ne pas présenter l'analyse interne comme un avis
juridique.

## 6. Exécuter N0–N4 uniquement comme audits

Si et seulement si l'entry gate passe, traiter :

### N0 — Commercial readiness audit

- consolider verdict, niveau de claim autorisé, date, propriété, blockers et approbateurs ;
- définir le produit étudié sans sélectionner arbitrairement un modèle commercial ;
- vérifier que le research core et l'exécution restent séparés.

### N1 — Legal/regulatory classification

- distinguer research, analytics, recommendation, personalized advice et execution ;
- identifier juridiction, utilisateurs, personnalisation, marketing, records et privacy ;
- préparer les questions et documents pour le conseil professionnel.

### N2 — Market-data licensing review

- construire une matrice par fournisseur et output : use/display/redistribution/derived/
  non-display/storage/commercial ;
- couvrir OPRA, broker, historique, exchange, news/events, FRED, SEC et datasets dérivés ;
- bloquer tout output dont les droits ne sont pas confirmés par écrit.

### N3 — IP/security separation

- inventorier code, modèles, paramètres, datasets, secrets, licences et propriété ;
- proposer la frontière repo public / moteur privé / API, sans l'implémenter ;
- produire threat model, data flows et risques de reproduction/redistribution.

### N4 — Multi-underlying validation

- garder TTWO comme laboratoire jusqu'à validation ;
- sélectionner 5–10 sous-jacents seulement via liquidité, couverture, spreads, OI, compatibilité,
  qualité et régimes ;
- exiger un protocole prospectif comparable sans modifier Python par ticker ;
- séparer les modules GTA/Take-Two/Rockstar du critère de généricité.

Ces audits ne donnent pas l'autorisation de commencer N5.

## 7. Produire le commercial GO/NO-GO

Avant N5, créer `COMMERCIAL_GO_NO_GO.md` avec une ligne de preuve, owner, reviewer, date,
blockers et décision pour chaque dimension :

- quantitative edge et niveau de claim ;
- data rights ;
- regulatory ;
- security/privacy ;
- market/customer evidence ;
- unit economics ;
- product differentiation ;
- IP.

Verdicts autorisés :

- `GO` : tous les gates critiques passent ;
- `CONDITIONAL_GO` : seulement des travaux préparatoires explicitement bornés ;
- `NO_GO` : ne pas construire le SaaS.

Un `GO` doit être validé explicitement par l'utilisateur après les revues professionnelles.
Sans cette validation, s'arrêter avant N5.

## 8. Hypothèses à tester, jamais à hard-coder

Comparer sans choisir d'avance :

- Retail research SaaS ;
- Professional analytics ;
- B2B/API/white label.

Tester comme hypothèses datées :

- Retail : EUR 49–199/mois ;
- Professional : EUR 300–1 500/mois ;
- B2B/API : EUR 15 000–100 000+/an ;
- tiers possibles : Free, Investor, Pro, Quant/API, Enterprise.

Réaliser des interviews et une recherche de pricing. Calculer MRR, ARR, cost per user, gross et
contribution margin, ARPU, CAC, LTV, churn, retention et sensibilité. Distinguer clairement
scénarios et prévisions.

La proposition de valeur doit décrire le résultat client—par exemple comparer rendement, risque
sévère, preuves, accord des modèles et exécution—et non vendre Heston, GARCH, SVI ou Monte Carlo
comme moat.

## 9. Architecture conceptuelle à préserver

Si un futur `GO` autorise N5, partir de l'hypothèse minimale :

```text
providers → private data layer → private quant core → versioned research API
                                                       ↓
                                             web / mobile / API
```

- moteur quantitatif privé et server-side ;
- billing → entitlement → product access, jamais billing → quant logic ;
- `model_version`, `api_version` et `product_version` séparées ;
- pas de microservices ou cloud complexe sans benchmark ;
- P50/P95/P99 pour génération, pricing, simulation, ingestion et dashboards ;
- auth, organisations, rôles, clés API, quotas et audit uniquement après autorisation ;
- fail-closed `DATA_UNAVAILABLE` pour données absentes, stale, croisées ou non licenciées.

Le produit doit afficher les cinq scores, leurs couvertures et les métriques brutes, notamment
la severe-loss ladder. Ne jamais commercialiser un score magique ou une UX réduite à BUY/SELL.

## 10. Documents à produire pendant Phase N

Créer seulement au moment où leur phase est autorisée :

```text
COMMERCIAL_GO_NO_GO.md
docs/commercial/OPRA_COMMERCIAL_DATA_RIGHTS.md
docs/commercial/PRICING_RESEARCH.md
docs/commercial/regulatory/PRODUCT_CLASSIFICATION.md
docs/commercial/regulatory/JURISDICTION_MATRIX.md
docs/commercial/regulatory/DATA_RIGHTS.md
docs/commercial/regulatory/RISK_DISCLOSURES.md
docs/commercial/regulatory/USER_SUITABILITY_BOUNDARY.md
docs/commercial/regulatory/MARKETING_CLAIMS_POLICY.md
docs/commercial/regulatory/RECORD_RETENTION.md
MODEL_CHANGE_LOG.md
```

Ne pas créer des documents vides pour simuler l'avancement. Chaque document doit citer des preuves
actuelles, responsables, limites, questions ouvertes et validations requises.

## 11. N5–N15 après GO uniquement

Après `GO` explicite seulement :

```text
N5  SaaS product architecture
N6  Authentication / organizations
N7  Subscription / billing
N8  Web product
N9  API product
N10 Internal admin / monitoring
N11 Private alpha
N12 Closed beta
N13 Paid beta
N14 General availability
N15 Enterprise / B2B
```

Chaque transition exige des critères de sortie et une validation. Private alpha mesure UX, bugs,
compréhension, qualité, latence et communication du risque. Closed beta mesure willingness-to-pay,
rétention, usage, valeur et support. Paid beta mesure prix réel, conversion, churn, support et
unit economics. General availability exige stabilité, licences, juridique, sécurité, privacy,
monitoring, support, recovery et claims approuvés.

## 12. Model, data, and product governance

Préserver le dataset prospectif : snapshot, quotes, candidat universe, ranking, cinq scores,
prédiction, décision gelée, résultat futur séparé, P&L, spread, slippage, erreur, provenance,
hashes, versions, timestamp et régime.

Tout changement quantitatif matériel suit :

```text
research → validation → shadow → paper → approval → deployment
```

Surveiller market-data health, model/API health, Brier, ECE, score/risk calibration, monotonicité,
model disagreement, execution slippage et incidents. En cas de drift, dégrader Evidence ou
suspendre l'output concerné.

Ne publier ni raw licensed data, ni dataset complet, ni secrets, ni calibration interne. Vérifier
les droits des outputs dérivés avant exposition.

## 13. Claims, privacy, security, and support

Interdire sans preuve appropriée : guaranteed returns, beats the market, AI predicts the market,
90% profitable, best option, risk free. Toute claim quantitative indique période, échantillon,
méthode, frais, limites et type de preuve.

Ne jamais considérer un disclaimer comme substitut à la classification réglementaire. Identifier
la frontière de personnalisation avant l'UX. Minimiser email, billing, IP, usage, préférences de
risque, portefeuille et informations financières.

Avant lancement : threat model, secrets, authn/authz, tenant isolation, rate limits, encryption,
logs, backups/restores, dependency audit, incident response, vulnerability disclosure, FAQ,
support, billing support, data issue reporting et documentation utilisateur.

## 14. Format de sortie attendu

Répondre en français avec :

```text
PHASE N ENTRY STATUS
FINAL QUANTITATIVE VERDICT
EVIDENCE AUDIT
FACTS / HYPOTHESES / DECISIONS
N0–N4 STATUS
QUANTITATIVE CLAIM BOUNDARY
DATA-RIGHTS STATUS
REGULATORY STATUS
IP / SECURITY STATUS
MULTI-UNDERLYING STATUS
MARKET / PRICING STATUS
UNIT-ECONOMICS STATUS
COMMERCIAL GO / CONDITIONAL_GO / NO_GO
EXACT BLOCKERS
FILES CREATED
FILES MODIFIED
SOURCES USED
VALIDATIONS REQUESTED
NEXT AUTHORIZED ACTION
```

Si le résultat n'est pas `GO`, ne pas commencer N5. Si le résultat est `GO`, demander encore
l'autorisation explicite de l'utilisateur avant toute implémentation commerciale.

---

End of future resume prompt.
