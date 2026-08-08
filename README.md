# Take Two Options

Read-only, generic, knowledge-driven option research for bounded-risk trade
requests. The active pipeline loads provenance-aware recipes, enumerates listed
strikes and expirations, applies executable bid/ask and whole-contract budget
constraints, runs separate conditional simulations, validates hard gates, then
uses Pareto ranking. `NO_TRADE` and `BLOCKED_INSUFFICIENT_DATA` are first-class
outcomes.

```bash
ttwo-options knowledge validate --knowledge-dir research/knowledge_items
ttwo-options knowledge compile \
  --knowledge-dir research/knowledge_items \
  --catalog-out research/strategy_catalog/catalog.json
ttwo-options data refresh --ticker TTWO
ttwo-options trade analyze \
  --request configs/trades/ttwo_gta6_1000eur.yaml \
  --refresh-data \
  --report-dir reports/latest
ttwo-options trade compare --report reports/latest/decision_report.json
ttwo-options trade ibkr-ticket \
  --report reports/latest/decision_report.json \
  --candidate-id <ID> \
  --mode preview
ttwo-options position monitor \
  --position <POSITION_FILE> \
  --refresh-data \
  --report-dir reports/latest/position
ttwo-options thesis-scan \
  --ticker TTWO \
  --direction bullish \
  --budget-eur 1000 \
  --catalyst-date 2026-11-19 \
  --expiration-buffer-days 45 \
  --target-prices 220,250,280,300,330,360 \
  --scenario-probabilities 0.10,0.15,0.20,0.20,0.20,0.15 \
  --max-loss-eur 1000 \
  --top 3 \
  --current-chain fixtures/thesis_scanner/ttwo_synthetic_chain.json \
  --json-out reports/examples/v10_thesis_scan.json \
  --markdown-out reports/examples/v10_thesis_scan.md \
  --html-out reports/examples/v10_thesis_scan.html
ttwo-options intelligence-run \
  --base-report reports/examples/v10_thesis_scan.json \
  --policy configs/intelligence/v11.yaml \
  --events fixtures/v11/events_empty.json \
  --profile fast_fixture \
  --json-out reports/v11/latest.json \
  --markdown-out reports/v11/latest.md \
  --html-out reports/v11/latest.html
ttwo-options calibration report \
  --dataset fixtures/v11/historical_calibration.example.json \
  --walk-forward fixtures/v11/walk_forward.example.json \
  --output reports/v11/calibration/offline_validation.json
ttwo-options position replay \
  --trajectory fixtures/v11/position_trajectory.example.json \
  --output reports/v11/position_trajectory.json
```

The package contains no live-order submission, modification, cancellation, or
exercise capability. V10 creates a usable IBKR preview only after its gates.
V11 may also emit a deliberately blocked preview dossier so every missing
broker fact remains visible. Every artifact keeps `transmit=false`,
`what_if=true`, human confirmation, and `order_capability=forbidden`.

`thesis-scan` is the V10.1 bullish-thesis scanner. It exhaustively constructs
configured long calls (including the LEAPS maturity class), bull call spreads,
and symmetric call butterflies over listed quotes. It never invents scenario
probabilities: omit `--scenario-probabilities` and expected P&L/probability of
success remain null. Its three rankings are independent and visible
(`prudent`, `balanced`, `aggressive`); weak V9 evidence lowers the displayed
confidence but does not silently veto thesis mode.

The V10.1 output schema adds Python-computed decision metrics and an accessible
Top N dashboard. `--top 3`, `--top 5`, or `--top 10` controls the maximum
number of accordion entries shown independently in each profile. JavaScript
only selects and formats report values; option risk, scenario P&L, ratios,
contractual limits, and ×2/×3/×5 terminal thresholds are computed in Python.

`intelligence-run` is the modular V11 research layer over a stable V10.1
structure report. It keeps V10.1 as the construction and QuantLib American
control engine, then adds:

- a provenance-aware data hub with read-only SEC EDGAR, FRED, Take-Two RSS,
  Google Trends alpha, market-calendar, and IBKR/OPRA adapter boundaries;
- deduplicated Bayesian scenario updates with evidence-family caps and a full
  prior/likelihood/weight/posterior audit;
- four regimes crossed with GBM, Dupire local volatility, Heston, and
  Heston-plus-jumps simulations;
- dynamic covariance diagnostics, exact whole-contract allocation under hard
  constraints, and explicit cash/`NO_TRADE` alternatives;
- cost, adverse, rupture, CVaR, holdout, and paper-trading promotion gates;
- explainable position monitoring and preview-only IBKR combo artifacts.

The default V11 fixture is a reproducible integration demonstration. Its
priors, likelihoods, stochastic parameters, synthetic option chain, and local
volatility fallbacks are experimental inputs, not calibrated forecasts or a
trade recommendation. Live connectors are implemented as opt-in ports but are
not contacted by the default CLI run.

V7–V9 are isolated under `experiments/legacy/`; their inspected holdouts are
marked contaminated under `validation/contaminated_holdouts/`.

See [product contract](docs/product/PRODUCT_CONTRACT.md),
[current architecture](docs/architecture/CURRENT_ARCHITECTURE.md),
[V10.1 architecture](docs/architecture/V10_BULLISH_THESIS_SCANNER.md),
[V11 architecture](docs/architecture/V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md),
[readiness](docs/READINESS.md),
[validation plan](docs/VALIDATION_PLAN.md),
[calibration](docs/CALIBRATION.md),
[backtesting](docs/BACKTESTING.md),
[model risk](docs/MODEL_RISK.md),
[data provenance](docs/DATA_PROVENANCE.md),
[security](docs/SECURITY.md),
[V10.1 data guide](docs/thesis_scanner_data_guide.md),
[migration](docs/MIGRATION.md), and [limitations](docs/LIMITATIONS.md).

## A. Ce qui fonctionne aujourd’hui hors ligne

- construction exhaustive V10.1 des calls, bull call spreads et butterflies
  configurés sur les contrats fournis ;
- coût prudent au bid/ask, payoff exact, perte maximale et contrôle américain
  QuantLib ;
- ingestion point-in-time avec provenance, cutoff, fraîcheur, unités, hashes,
  doublons et états de connecteur ;
- normalisation déterministe des événements avec preuve de règle, expiration,
  revue humaine, clusters de doublons et contradictions ;
- waterfall bayésien auditable, caps par famille et sensibilité du posterior ;
- simulations multi-modèles reproductibles, diagnostics de convergence,
  comparaison de robustesse et stress explicites ;
- allocation entière avec budget, perte, concentration, liquidité, Greeks,
  cash et `NO_TRADE` ;
- surveillance advisory à partir de snapshots et replay d’une trajectoire
  synthétique multi-date ;
- rapports JSON, Markdown et HTML autonome avec résumé machine, hashes et
  statuts de readiness ;
- preview strictement non transmissible : `transmit=false`, `what_if=true`,
  confirmation humaine et `order_capability=forbidden`.

`production_ready_offline` décrit uniquement un invariant logiciel déterministe.
Il ne qualifie ni une probabilité de marché, ni une stratégie, ni un rendement.

## B. Ce qui est expérimental

- priors, likelihoods, probabilités et scores de confiance ;
- paramètres Heston, paramètres de sauts et hypothèses de régimes ;
- surface de volatilité locale construite depuis une entrée synthétique ou
  partielle ;
- simulations, robustesse et allocation alimentées par des fixtures ;
- seuils de sortie, stress, profil de risque et prévisions issues de fixtures.

Ces éléments portent `experimental_offline` ou `fixture_only`. Ils ne peuvent pas
être promus par un rang, un score ou un résultat in-sample.

## C. Ce qui nécessite des données historiques réelles

- calibration des probabilités, likelihoods, régimes et modèles ;
- historique point-in-time des contrats, surfaces, quotes bid/ask, spot, taux,
  dividendes, FX, événements et coûts ;
- splits rolling/expanding, embargo, backtests walk-forward et holdout non
  contaminé ;
- Brier score, log-loss, ECE, courbes de calibration et pouvoir prédictif ;
- comparaison hors échantillon à cash, sous-jacent, call ATM, call à delta
  fixe, spread standard, aléatoire admissible et `NO_TRADE`.

Le framework JSON/CSV/Parquet optionnel est implémenté. Sans dataset réel
autorisé, il renvoie `BLOCKED_MISSING_CALIBRATION_DATA`. Une fixture reste
`FIXTURE_ONLY_NOT_CALIBRATED` ou `FIXTURE_ONLY_NOT_VALIDATED`.

## D. Ce qui nécessite une API live

- chaîne OPRA, spot et quotes horodatées ;
- bid/ask, open interest, volume, surface d’IV et Greeks live ou recalculés ;
- découverte et qualification des contrats ;
- quotes combo IBKR, marge et commissions what-if ;
- fraîcheur, reconnexion, rate limits, état des ordres et surveillance
  intraday.

Le port IBKR/OPRA est `adapter_ready_not_connected`. Le CLI par défaut n’ouvre
aucune session. La roadmap est détaillée dans
[LIVE_DATA_ROADMAP.md](docs/LIVE_DATA_ROADMAP.md) et
[IBKR_OPRA_ROADMAP.md](docs/IBKR_OPRA_ROADMAP.md).

## E. Ce qui doit être terminé avant commercialisation

- [ ] licence et droits de redistribution des données ;
- [ ] données historiques autorisées ;
- [ ] calibration sur données réelles ;
- [ ] backtest walk-forward ;
- [ ] holdout non contaminé ;
- [ ] probabilités correctement calibrées ;
- [ ] paper trading ;
- [ ] combo quotes IBKR ;
- [ ] contrôle des coûts réels ;
- [ ] surveillance live ;
- [ ] tests de charge ;
- [ ] sécurité ;
- [ ] audit externe ;
- [ ] mentions réglementaires ;
- [ ] conditions d’utilisation ;
- [ ] politique de confidentialité ;
- [ ] gestion des abonnements ;
- [ ] monitoring de production ;
- [ ] support utilisateur ;
- [ ] plan de reprise ;
- [ ] aucune promesse de rendement.

La checklist probante et la frontière réglementaire sont dans
[COMMERCIALIZATION_CHECKLIST.md](docs/COMMERCIALIZATION_CHECKLIST.md) et
[REGULATORY_BOUNDARY.md](docs/REGULATORY_BOUNDARY.md).

## F. Conditions de promotion

Les gates autorisés, sans aucun gate d’exécution automatique, sont :

1. `RESEARCH_ONLY`
2. `OFFLINE_VALIDATED`
3. `HISTORICALLY_CALIBRATED`
4. `WALK_FORWARD_PASSED`
5. `PAPER_TRADING`
6. `LIVE_DATA_READ_ONLY`
7. `HUMAN_CONFIRMED_PREVIEW`
8. `COMMERCIAL_RESEARCH_PRODUCT`

Chaque gate exige critères d’entrée et de sortie, métriques minimales, données,
responsable humain et preuves archivées. Les seuils non encore approuvés restent
`draft_to_validate`. La matrice complète se trouve dans
[READINESS.md](docs/READINESS.md) ; le paper trading dans
[PAPER_TRADING_PLAN.md](docs/PAPER_TRADING_PLAN.md).

## Comment le bot raisonne

Le moteur ne cherche pas « la meilleure option » en une seule étape. Il
conserve des frontières explicites entre :

1. les observations datées et leur provenance ;
2. les hypothèses configurées ;
3. les scénarios conditionnels ;
4. les structures contractuelles réellement cotées ;
5. les simulations et leurs désaccords ;
6. les contraintes dures ;
7. le classement de recherche ;
8. la validation statistique ;
9. l’autorisation d’exécution, qui reste absente.

La méthode décisionnelle publique est :

```text
faits datés
  -> contrôles de qualité et de disponibilité au cutoff
  -> événements normalisés et dédupliqués
  -> distribution bayésienne conditionnelle
  -> structures V10.1 ayant passé les veto contractuels
  -> quatre modèles x quatre régimes
  -> valorisation avec règles de sortie
  -> comparaison de robustesse
  -> allocation entière sous contraintes
  -> stress, holdout et paper gates
  -> NO_TRADE / watchlist / paper_review
  -> preview humaine non transmissible
```

Principes non négociables :

- une donnée manquante n’est jamais remplacée par une valeur « plausible » ;
- une hypothèse reste identifiée comme hypothèse ;
- un même fait repris par plusieurs articles ne compte qu’une fois ;
- les modèles restent séparés avant toute agrégation ;
- un score ne peut pas annuler un veto ;
- le cash et `NO_TRADE` sont toujours des solutions admissibles ;
- un résultat synthétique ou contaminé ne peut pas être promu ;
- aucune probabilité, formule ou allocation n’accorde le droit d’envoyer un
  ordre.

## Architecture mathématique

### Notation

| Symbole | Définition |
| --- | --- |
| \(S_t\) | cours de TTWO au temps \(t\) |
| \(K\) | strike |
| \(T\) | maturité en années |
| \(r\) | taux sans risque continu |
| \(q\) | rendement de dividende continu |
| \(\sigma\) | volatilité |
| \(M\) | multiplicateur contractuel, normalement 100 |
| \(q_i\) | quantité de la jambe \(i\) |
| \(s_i\) | signe de la jambe : \(+1\) long, \(-1\) short |
| \(C\) | coût total de la position, frais et slippage inclus |
| \(B\) | budget |
| \(x_i\) | nombre entier d’unités de la stratégie \(i\) |
| \((z)^+\) | \(\max(z,0)\) |

Les montants optionnels sont calculés en USD, puis convertis en EUR avec :

$$
\text{montant}_{EUR} =
\frac{\text{montant}_{USD}}{\text{EURUSD}}.
$$

Le taux FX est daté et audité. Ce n’est pas un taux d’exécution garanti.

## 1. Données, cutoff et provenance

Une observation unifiée contient au minimum :

```text
series, timestamp, retrieved_at, cutoff, value, unit, provider,
source_uri ou source_id, domain, quality, freshness_status,
point_in_time_valid, raw_hash, license_or_usage_notes, metadata
```

Une source contient :

```text
provider, URI, retrieved_at, quality, conditions d’usage, hash, notes
```

La règle point-in-time est :

$$
t_{\text{observation}} \leq t_{\text{cutoff}}.
$$

RSS, Google Trends, calendrier de marché, facteurs historiques et quotes IBKR
postérieurs au cutoff sont exclus. Une quote IBKR sans timestamp est exclue.
Les statuts `not_configured`, `unavailable`, `failed`, `partial` et `ready`
restent distincts.

Connecteurs disponibles :

- seed normalisé V10.1 ;
- JSON normalisé pour fixtures ou exports autorisés ;
- SEC EDGAR ;
- FRED ;
- RSS officiel Take-Two ;
- Google Trends API alpha ;
- calendrier de marché injecté ;
- IBKR/OPRA injecté, données de marché uniquement.

Important : les observations des connecteurs ne sont pas transformées
automatiquement en signaux. Une étape explicite de normalisation doit produire
les événements bayésiens décrits ci-dessous. Cela évite qu’un titre d’article
modifie directement une probabilité.

## 2. Prix d’entrée, liquidité et coûts

Pour chaque jambe :

$$
p_i^{entry} =
\begin{cases}
ask_i & \text{si la jambe est longue},\\
bid_i & \text{si la jambe est courte}.
\end{cases}
$$

Le midpoint diagnostique et le spread relatif sont :

$$
mid_i = \frac{bid_i + ask_i}{2},
\qquad
spread_i =
\frac{ask_i-bid_i}{mid_i}.
$$

Le débit prudent est :

$$
D = \sum_i s_i q_i M_i p_i^{entry}.
$$

Avec \(n_{sides}=\sum_i q_i\) :

$$
fees = n_{sides}\,fee_{side},
\qquad
slippage = n_{sides}\,slippage_{side},
$$

$$
C = D + fees + slippage.
$$

Le prix limite indicatif V10.1, pour les contrats standards ayant passé le
filtre \(M=100\), est :

$$
p_{limit} =
\frac{D+slippage}{100 \times N_{\text{unités}}}.
$$

Ce prix ne comprend pas les commissions et ne constitue pas une cotation combo.

Les principaux veto précèdent tout score :

- quote absente, non positive, croisée, future ou périmée ;
- spread relatif supérieur au seuil ;
- échéance antérieure au catalyseur plus buffer ;
- strike hors de la plage de moneyness ;
- open interest ou volume sous un seuil connu ;
- multiplicateur ou livrable inconnu/non standard ;
- débit, perte maximale ou nombre de contrats hors limites ;
- structure non bornée ou incompatible avec la thèse ;
- spread combo synthétique excessif ;
- FX ou taux venant du futur.

Une valeur inconnue peut produire une watchlist explicite ; une violation
connue produit un blocage.

## 3. Payoff contractuel des structures

La valeur intrinsèque d’une jambe à l’échéance est :

$$
I_i(S_T) =
\begin{cases}
(S_T-K_i)^+ & \text{call},\\
(K_i-S_T)^+ & \text{put}.
\end{cases}
$$

La valeur terminale et le P&L sont :

$$
V_T(S_T)=\sum_i s_i q_i M_i I_i(S_T),
\qquad
P\&L_T(S_T)=V_T(S_T)-C.
$$

### Long call

Pour \(q\) calls de strike \(K\) :

$$
P\&L_T=qM(S_T-K)^+-C.
$$

$$
PerteMax=C,
\qquad
BreakEven=K+\frac{C}{qM}.
$$

Le gain contractuel est non plafonné.

### Bull call spread

Avec \(K_1<K_2\), long \(K_1\) et short \(K_2\) :

$$
P\&L_T=qM\left[(S_T-K_1)^+-(S_T-K_2)^+\right]-C.
$$

$$
PerteMax=C,
\qquad
GainMax=qM(K_2-K_1)-C,
$$

$$
BreakEven=K_1+\frac{C}{qM}.
$$

### Call butterfly symétrique

Avec \(K_2-K_1=K_3-K_2\), ratios \(+1/-2/+1\) :

$$
P\&L_T=qM\left[
(S_T-K_1)^+
-2(S_T-K_2)^+
+(S_T-K_3)^+
\right]-C.
$$

$$
PerteMax=C,
\qquad
GainMax=qM(K_2-K_1)-C.
$$

Sous les hypothèses usuelles d’un débit inférieur à la largeur d’aile :

$$
BreakEvenBas=K_1+\frac{C}{qM},
\qquad
BreakEvenHaut=K_3-\frac{C}{qM}.
$$

Le moteur générique ne suppose pas ces formules à la main pour trouver tous les
break-even : il évalue le payoff linéaire par morceaux aux strikes, détecte les
changements de signe et interpole les racines.

Pour les seuils ×2, ×3 et ×5, il résout les spots tels que :

$$
V_T(S_T)=mC,\qquad m\in\{2,3,5\}.
$$

Le gain net correspondant est \((m-1)C\). Une structure plafonnée peut rendre
un seuil impossible.

## 4. Valorisation Black-Scholes et contrôle américain

Le contrôle européen utilise :

$$
d_1 =
\frac{\ln(S/K)+(r-q+\frac{1}{2}\sigma^2)T}
{\sigma\sqrt{T}},
\qquad
d_2=d_1-\sigma\sqrt{T}.
$$

Call :

$$
C_{BS}=Se^{-qT}N(d_1)-Ke^{-rT}N(d_2).
$$

Put :

$$
P_{BS}=Ke^{-rT}N(-d_2)-Se^{-qT}N(-d_1).
$$

À l’échéance, le moteur revient exactement à l’intrinsèque.

V10.1 utilise QuantLib et un schéma finite-difference américain pour les
valorisations avant échéance. L’équation de continuation sous-jacente est :

$$
\frac{\partial V}{\partial t}
+\frac{1}{2}\sigma^2S^2\frac{\partial^2V}{\partial S^2}
+(r-q)S\frac{\partial V}{\partial S}
-rV=0,
$$

avec la contrainte américaine :

$$
V(S,t)\geq payoff(S).
$$

Le moteur compare aussi la valeur américaine à un benchmark européen. La prime
d’exercice anticipé diagnostique est :

$$
Premium_{early}=V_{American}-V_{European}.
$$

Black-Scholes reste un contrôle rapide ; il n’est jamais présenté comme la
vérité du marché.

## 5. Greeks

Les Greeks américains V10.1 sont calculés autour du même moteur QuantLib par
différences finies.

Avec \(h_S=\max(0.001S,0.01)\) :

$$
\Delta \approx
\frac{V(S+h_S)-V(S-h_S)}{2h_S},
$$

$$
\Gamma \approx
\frac{V(S+h_S)-2V(S)+V(S-h_S)}{h_S^2}.
$$

Le theta est une variation sur un jour calendaire :

$$
\Theta \approx V(t+1\ jour)-V(t).
$$

Avec un pas de volatilité
\(h_\sigma=\min(0.01,0.25\sigma)\), le vega par point de volatilité est :

$$
Vega \approx
\frac{V(\sigma+h_\sigma)-V(\sigma-h_\sigma)}
{2h_\sigma}\times0.01.
$$

Avec \(h_r=0.001\), le rho par point de taux est :

$$
Rho \approx
\frac{V(r+h_r)-V(r-h_r)}
{2h_r}\times0.01.
$$

Les Greeks nets de la stratégie sont :

$$
Greek_{position} =
\sum_i s_i q_i M_i Greek_i.
$$

Ils sont des sensibilités locales, pas des prévisions de P&L exactes.

## 6. Scénarios déterministes V10.1

V10.1 valorise chaque candidat :

- aujourd’hui ;
- à +30, +60 et +90 jours lorsque ces dates précèdent l’échéance ;
- à la date du catalyseur ;
- à l’échéance ;
- sur les objectifs utilisateur et une grille de spots ;
- avec IV ×0,80, ×1,00 et ×1,20.

Pour une date \(d\), un spot \(S\) et un multiplicateur d’IV \(m_\sigma\) :

$$
V(S,d,m_\sigma)=
\sum_i s_iq_iM_i
V_{American}(S,K_i,T_i-d,m_\sigma\sigma_i,r,q).
$$

$$
P\&L(S,d,m_\sigma)=V(S,d,m_\sigma)-C.
$$

L’attribution séquentielle est :

$$
EffetSousJacent=V(S,t_0,\sigma)-V(S_0,t_0,\sigma),
$$

$$
EffetTemps=V(S,d,\sigma)-V(S,t_0,\sigma),
$$

$$
EffetIV=V(S,d,m_\sigma\sigma)-V(S,d,\sigma),
$$

$$
EffetExécution=V(S_0,t_0,\sigma)-C,
$$

$$
Résiduel=P\&L-\sum Effets.
$$

Si l’utilisateur fournit des probabilités \(p_j\) pour chaque objectif
\(S_j\), avec \(\sum_jp_j=1\) :

$$
E[P\&L]=\sum_jp_jP\&L(S_j,t_{catalyseur},IV_{stable}),
$$

$$
P(succès)=\sum_{j:P\&L_j>0}p_j.
$$

Sans probabilités utilisateur, ces deux valeurs restent `null`. V10.1 ne les
invente pas.

## 7. Classements déterministes V10.1

Chaque critère est ramené entre 0 et 1. Les opérateurs principaux sont :

$$
clamp(z)=\min(\max(z,0),1),
$$

$$
normalize^+(z)=
\frac{\max(z,0)}{1+\max(z,0)}.
$$

Exemples exacts :

$$
ReducedLoss=clamp\left(1-\frac{PerteMax}{Budget_{USD}}\right),
$$

$$
SpreadQuality=
clamp\left(1-\frac{spread_{relatif}}{spread_{max}}\right),
$$

$$
ThetaModeration=
clamp\left(
1-\frac{|\Theta|/C}{0.02}
\right),
$$

$$
CostQuality=clamp\left(1-\frac{C}{Budget_{USD}}\right),
$$

$$
BullishExposure=
clamp\left(
\frac{\Delta_{net}}{100\times contratsLongs}
\right).
$$

La liquidité d’une jambe combine :

$$
Liquidity_i =
0.50\,SpreadQuality_i+
0.35\,OIQuality_i+
0.15\,VolumeQuality_i.
$$

Avec :

$$
OIQuality_i=
\begin{cases}
0.35 & \text{si OI est manquant},\\
1 & \text{si }OI_{min}=0,\\
clamp\left(\frac{OI_i}{5OI_{min}}\right) & \text{sinon},
\end{cases}
$$

et la même règle pour le volume.

La proximité du break-even utilise :

$$
BreakEvenProximity=
clamp\left(
1-
\frac{|BE_{nearest}-S_0|}
{\max(S_{target,max}-S_0,0.1S_0,1)}
\right).
$$

La part de scénarios gagnants est :

$$
ScenarioBreadth=
\frac{
\#\{targets:P\&L_{target}/PerteMax>0\}
}{
\#targets
}.
$$

Les autres critères principaux sont :

$$
PayoffRatio=
normalize^+\left(
\frac{GainMax}{PerteMax}
\right),
$$

ou, pour un gain non borné, le meilleur rendement parmi les objectifs ;

$$
Convexity=normalize^+(\max(\Gamma_{net},0)),
$$

$$
ModeledReturn=
normalize^+\left(
\max_j\frac{P\&L_{target,j}}{PerteMax}
\right).
$$

Pour un butterfly de centre \(K_2\) et de largeur d’aile \(W\) :

$$
ButterflyTargeting=
clamp\left(
1-\frac{\min_j|S_{target,j}-K_2|}{\max(W,1)}
\right).
$$

La préférence structurelle interne vaut 1,00 pour un bull spread, 0,65 pour un
butterfly et 0,45 pour un long call. La confiance historique V10.1 par défaut
vaut 0,35 en raison des anciens échantillons faibles/contaminés.

Le score d’un profil est :

$$
Score_{profil} =
100
\frac{\sum_c w_{profil,c}\,critère_c}
{\sum_c w_{profil,c}}.
$$

Poids `prudent` :

| Critère | Poids |
| --- | ---: |
| perte réduite | 0,24 |
| break-even proche | 0,16 |
| liquidité | 0,15 |
| qualité du spread | 0,14 |
| theta modéré | 0,12 |
| préférence bull spread | 0,10 |
| largeur des scénarios gagnants | 0,05 |
| confiance historique | 0,04 |

Poids `balanced` :

| Critère | Poids |
| --- | ---: |
| ratio gain/risque | 0,18 |
| largeur des scénarios gagnants | 0,16 |
| liquidité | 0,14 |
| exposition haussière | 0,13 |
| capital non consommé | 0,12 |
| break-even proche | 0,10 |
| theta modéré | 0,09 |
| qualité du spread | 0,05 |
| confiance historique | 0,03 |

Poids `aggressive` :

| Critère | Poids |
| --- | ---: |
| convexité | 0,22 |
| rendement modélisé | 0,20 |
| exposition haussière | 0,18 |
| largeur des scénarios gagnants | 0,13 |
| centrage butterfly | 0,10 |
| ratio gain/risque | 0,08 |
| liquidité | 0,05 |
| confiance historique | 0,04 |

Les scores sont déterministes et explicables. Ils organisent les candidats
ayant déjà passé les filtres ; ils ne constituent pas des probabilités.

Le pool V11 n’utilise pas un classement V10.1 unique. Il prend le rang 1 de
`prudent`, puis de `balanced`, puis d’`aggressive`, ensuite le rang 2 de chacun,
et ainsi de suite. Les doublons sont retirés jusqu’à atteindre la taille
configurée, six candidats par défaut. Cette sélection round-robin évite qu’un
seul profil fournisse tout le pool.

## 8. Mise à jour séquentielle des croyances configurées V11

Les scénarios par défaut sont :

| Scénario | Prior expérimental | Régime |
| --- | ---: | --- |
| marché de base | 35 % | neutral |
| succès GTA | 35 % | thesis |
| retard ou guidance en baisse | 20 % | adverse |
| rupture | 10 % | rupture |

Pour un événement \(e\) et un scénario \(s\), la configuration fournit une
vraisemblance \(L_{e,s}=P(e\mid s)\).

Le poids demandé est :

$$
w_{requested}=baseWeight_e\times confidence_e.
$$

Avec un cap par famille :

$$
w_{remaining,f}=
\max(cap_f-used_f,0),
$$

$$
w_{effective}=
\begin{cases}
0 & \text{fait canonique déjà utilisé},\\
\min(w_{requested},w_{remaining,f}) & \text{sinon}.
\end{cases}
$$

La mise à jour fractionnelle configurée est :

$$
\widetilde p_s =
p_s L_{e,s}^{w_{effective}},
\qquad
p'_s=
\frac{\widetilde p_s}{\sum_j\widetilde p_j}.
$$

Pour un événement explicitement contradictoire :

$$
L'_{e,s}=\max(1-L_{e,s},10^{-6}).
$$

Un événement neutre reçoit un poids nul. Un événement sans règle compatible
est ignoré. Chaque update conserve prior, vraisemblances, poids demandé et
effectif, posterior, famille, confiance, déduplication, cap et sources
contradictoires.

Caps de familles par défaut :

| Famille | Cap |
| --- | ---: |
| source primaire entreprise | 1,00 |
| réglementaire | 0,80 |
| fondamentaux | 0,75 |
| marché | 0,60 |
| options | 0,60 |
| attention | 0,30 |
| actualités | 0,25 |
| social | 0,15 |

Table de vraisemblance active livrée, dans l’ordre
`market_base / gta_success / delay_or_guidance_down / rupture` :

| Événement | Famille | Poids de base | Vraisemblances |
| --- | --- | ---: | --- |
| retard GTA confirmé | source primaire | 1,00 | 0,05 / 0,01 / 0,90 / 0,35 |
| date maintenue | source primaire | 0,80 | 0,55 / 0,80 / 0,15 / 0,30 |
| guidance en hausse | fondamentaux | 0,80 | 0,45 / 0,80 / 0,10 / 0,35 |
| guidance en baisse | fondamentaux | 0,80 | 0,25 / 0,08 / 0,80 / 0,50 |
| achat d’initié | réglementaire | 0,40 | 0,45 / 0,65 / 0,25 / 0,35 |
| intérêt de recherche en hausse | attention | 0,25 | 0,50 / 0,65 / 0,35 / 0,50 |
| spike d’IV | options | 0,35 | 0,30 / 0,55 / 0,50 / 0,80 |
| flux options haussier | options | 0,30 | 0,45 / 0,65 / 0,25 / 0,45 |

Le schéma accepte aussi d’autres types d’événements, mais un événement sans
règle dans cette table n’affecte pas le posterior.

Les priors, likelihoods et caps sont des entrées `calibration_required`, pas
des fréquences historiques validées. Malgré les noms de schémas historiques
`Bayesian*`, cette distribution porte la sémantique `configured_heuristic_belief` : elle n'est
pas le posterior d'un modèle statistique ajusté.

La couche séquentielle ajoute un contrat point-in-time à chaque événement. Les dépendances sont
déclarées comme `same_fact`, `derived_from`, `shared_driver` ou `contradicts`. Un même fait ou une
dérivation reçoit zéro nouveauté ; un driver partagé exige une décote explicite. Le graphe doit
être acyclique et chaque parent doit être disponible avant son enfant.

Les probabilités sont transportées dans un `ScenarioProbabilitySet` avec une origine exclusive :
`user_assumption`, `configured_heuristic`, `historical_estimate`, `market_implied` ou
`empirically_calibrated`. Cette dernière origine exige les hashes dataset, manifest et calibration,
la taille d'échantillon et une partition OOS. Chaque valeur centrale est accompagnée d'un intervalle
ou diagnostic d'incertitude.

Les scénarios événementiels déclarent séparément les chocs de spot, niveau d'IV, skew, courbure et
liquidité, leur durée/récupération, leur source, leur statut et leur mesure `P/Q`. Le mélange
conditionnel est :

$$
E_P[\mathrm{PnL}]=\sum_s p_s E_P[\mathrm{PnL}\mid s].
$$

Le moteur propage les bornes de croyance, calcule les probabilités de cible et de grosse perte,
et conserve `NO_TRADE`. Les plans `research_eligible_now`, `wait`, `revalue_*`, `exit_review_*` et
`roll_review` sont des règles humaines point-in-time ; toutes les sorties gardent
`order_capability=forbidden`.

Le rapport final peut être accompagné d'un `FinalDecisionEvidenceReport`. Ce sidecar exige les
estimations et intervalles, les probabilités et leur origine, hypothèses, scénarios favorables et
d'échec, risques de modèle, limites des données, raisons exactes du classement et de `NO_TRADE`.
Son grade suit une chaîne monotone et prend le plus faible composant requis :

`proposed → implemented → tested → numerically_validated → empirically_validated →
holdout_validated → paper_validated`.

Ce grade mesure la preuve disponible, pas la confiance dans un gain. La matrice
[`formula_lineage_matrix.md`](docs/research/formula_lineage_matrix.md) relie chaque formule à ses
sources, son code et ses tests ; le CI rejette les références orphelines. Les contradictions et
corrections restent visibles dans
[`errata_registry.yaml`](docs/research/errata_registry.yaml).

## 9. Volatilité locale Dupire

La chaîne V10.1 est interpolée sur une grille de moneyness :

$$
m=\frac{K}{S_0},
\qquad
k=\ln(m).
$$

La variance totale implicite est :

$$
w(k,T)=\sigma_{imp}(k,T)^2T.
$$

Le code estime par différences finies :

$$
\partial_Tw,\qquad \partial_kw,\qquad \partial_{kk}w.
$$

Avec le log-moneyness forward :

$$
y=k-(r-q)T,
$$

la variance locale implémentée est :

$$
\sigma_{loc}^2 =
\frac{\partial_Tw}{
\left(1-\frac{y}{w}\partial_kw\right)^2
-\frac{1}{4}\left(\frac{1}{4}+\frac{1}{w}\right)
(\partial_kw)^2
+\frac{1}{2}\partial_{kk}w
}.
$$

Si le dénominateur est instable, la variance non finie ou non positive, le
nœud revient à l’IV implicite observée. La volatilité produite est bornée entre
1 % et 300 %.

Conditions minimales :

- au moins deux échéances futures ;
- au moins trois strikes/moneyness ;
- calls avec IV disponible.

Le statut devient `partial` si un fallback est utilisé ou si la source n’est
pas OPRA. Les différences finies n’imposent pas globalement l’absence
d’arbitrage calendrier ou butterfly.

## 10. Covariance dynamique

Pour une matrice de facteurs alignés \(X\), chaque fenêtre utilise la covariance
échantillonnale :

$$
\Sigma_j =
\frac{1}{n_j-1}
\sum_{t=1}^{n_j}
(X_t-\bar X)(X_t-\bar X)^\top.
$$

Fenêtres par défaut :

- 20 séances, poids brut 0,45 ;
- 60 séances, poids brut 0,35 ;
- 252 séances, poids brut 0,20 ;
- périodes comparables d’événement, poids brut 0,25 si disponibles ;
- régime courant, poids brut 0,30 si disponible.

Les poids des fenêtres effectivement disponibles sont renormalisés :

$$
\alpha_j=\frac{a_j}{\sum_ka_k},
\qquad
\bar\Sigma=\sum_j\alpha_j\Sigma_j.
$$

Le shrinkage diagonal est :

$$
F=diag(diag(\bar\Sigma)),
$$

$$
\Sigma_{shrunk}=
(1-\delta)\bar\Sigma+\delta F,
$$

avec \(\delta=0.25\) par défaut.

Pour garantir une matrice positive semi-définie, si :

$$
\Sigma_{shrunk}=Q\Lambda Q^\top,
$$

les valeurs propres sont remplacées par :

$$
\lambda_i'=
\max\left(
\lambda_i,
10^{-10}\max(\max_j|\lambda_j|,1)
\right),
$$

$$
\Sigma_{PSD}=Q\Lambda'Q^\top.
$$

La corrélation publiée est :

$$
\rho_{ij}=
\frac{\Sigma_{ij}}
{\sqrt{\Sigma_{ii}\Sigma_{jj}}}.
$$

Le condition number est surveillé ; au-delà de \(10^8\), la matrice reste
signalée comme mal conditionnée.

Frontière actuelle : cette covariance factorielle est calculée et publiée
comme diagnostic. Elle n’est pas encore injectée dans les chocs des SDE ni
dans l’optimiseur d’allocation. L’optimiseur calcule séparément une covariance
empirique des P&L candidats.

## 11. Simulations stochastiques V11

Le run par défaut utilise 1 000 trajectoires, 90 pas, un horizon de 180 jours et
une seed de base `20260728`. Chaque couple modèle/régime reçoit une seed
déterministe distincte.

### Lemme d’Itô et lien avec les options

Pour une fonction d’option lisse \(V(S,t)\) et :

$$
dS_t=\mu S_tdt+\sigma S_tdW_t,
$$

le lemme d’Itô donne :

$$
dV=
\left(
\frac{\partial V}{\partial t}
+\mu S\frac{\partial V}{\partial S}
+\frac{1}{2}\sigma^2S^2
\frac{\partial^2V}{\partial S^2}
\right)dt
+\sigma S\frac{\partial V}{\partial S}dW_t.
$$

En notation Greeks, les premiers termes correspondent au theta, au delta et au
gamma. Avec un saut log \(Y\), un terme discret s’ajoute :

$$
\Delta V_{jump}=
V(S_{t^-}e^Y,t)-V(S_{t^-},t).
$$

Le bot n’utilise pas cette approximation seule pour produire le P&L
Monte-Carlo : il revalorise la position complète à chaque pas. Itô explique
le lien entre la SDE, les Greeks et l’attribution locale de monitoring.

### GBM

Équation continue :

$$
dS_t=\mu S_tdt+\sigma S_tdW_t.
$$

Incrément lognormal exact :

$$
S_{t+\Delta t}=
S_t\exp\left[
\left(\mu-\frac{1}{2}\sigma_t^2\right)\Delta t
+\sigma_t\sqrt{\Delta t}Z_t
\right],
\qquad Z_t\sim N(0,1).
$$

La variance passe linéairement de la variance initiale à la variance du régime
pendant les premiers 20 % des pas, puis reste constante :

$$
v_t=(1-a_t)v_0+a_tv_{regime},
\qquad
a_t=\min\left(\frac{step}{0.2\,steps},1\right).
$$

Cette transition évite de créer un gain de vega instantané à \(t=0\).

### Volatilité locale

$$
dS_t=\mu S_tdt+\sigma_{loc}(S_t,t)S_tdW_t.
$$

\(\sigma_{loc}\) est interpolée :

- linéairement entre les nœuds de moneyness ;
- linéairement entre les maturités ;
- à bord constant hors de la grille.

Le multiplicateur de volatilité du régime est appliqué progressivement pendant
les premiers 20 % des pas.

### Heston

$$
dS_t=\mu S_tdt+\sqrt{v_t}S_tdW_t^S,
$$

$$
dv_t=\kappa(\theta-v_t)dt+\xi\sqrt{v_t}dW_t^v,
$$

$$
dW_t^S\,dW_t^v=\rho\,dt.
$$

Le schéma full-truncation Euler utilise \(v_t^+=\max(v_t,0)\) :

$$
S_{t+\Delta t}=
S_t\exp\left[
\left(\mu-\frac{1}{2}v_t^+\right)\Delta t
+\sqrt{v_t^+}\sqrt{\Delta t}Z_t^S
\right],
$$

$$
v_{t+\Delta t}=
\max\left[
v_t^+
+\kappa(\theta_{regime}-v_t^+)\Delta t
+\xi\sqrt{v_t^+}\sqrt{\Delta t}Z_t^v,
0
\right].
$$

Les chocs sont corrélés par :

$$
Z_t^v=
\rho Z_t^S+
\sqrt{1-\rho^2}Z_t^\perp.
$$

La cible du régime est :

$$
\theta_{regime}=
\theta
\times volatilityMultiplier^2
\times(1+initialIVShift)^2.
$$

Les paramètres Heston livrés sont illustratifs, donc chaque sortie porte un
warning de sensibilité.

### Heston avec sauts

Le nombre de sauts par pas est :

$$
N_t\sim Poisson(\lambda\Delta t).
$$

Conditionnellement à \(N_t=n\), l’incrément log du saut est simulé comme :

$$
Y_t=n\mu_J+\sqrt{n}\sigma_JZ_J.
$$

Le compensateur de drift est :

$$
\kappa_J=
\lambda\left(
e^{\mu_J+\frac{1}{2}\sigma_J^2}-1
\right).
$$

Le spot devient :

$$
S_{t+\Delta t}=
S_t\exp\left[
\left(\mu-\kappa_J-\frac{1}{2}v_t^+\right)\Delta t
+\sqrt{v_t^+}\sqrt{\Delta t}Z_t^S
+Y_t
\right].
$$

Les valeurs sont bornées numériquement :

$$
10^{-8}\leq S_t\leq10^8,
\qquad
0\leq v_t\leq25.
$$

### Paramètres des régimes livrés

| Régime | Drift | Multiplicateur vol | Shift IV cible | Intensité sauts/an | Moyenne log saut | Vol log saut |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| neutral | 6 % | 1,00 | 0 % | 0,10 | 0 % | 5 % |
| thesis | 18 % | 1,05 | 10 % | 0,80 | 8 % | 10 % |
| adverse | −15 % | 1,30 | 25 % | 0,80 | −15 % | 12 % |
| rupture | 0 % | 1,80 | 50 % | 1,20 | −3 % | 30 % |

Ces valeurs sont des scénarios de recherche. Elles ne sont pas estimées comme
des fréquences ou paramètres TTWO validés.

## 12. Valorisation des trajectoires

Pour chaque trajectoire, chaque jambe est revalorisée avec le contrôle
Black-Scholes conditionnel :

$$
V_{position}(t)=
\sum_i s_iq_iM_i
V_{BS}\left(
S_t,K_i,T_i-t,\sqrt{v_t},r,q
\right).
$$

$$
P\&L_t=V_{position}(t)-C.
$$

Cette approximation permet une valorisation vectorisée de toutes les
trajectoires. Elle ne remplace pas les checkpoints américains QuantLib V10.1
pour l’exercice anticipé, les dividendes discrets, l’assignment ou le pin risk.

Pour accélérer ce calcul, la CDF normale est approchée par :

$$
t(x)=\frac{1}{1+0.2316419|x|},
\qquad
\phi(x)=\frac{e^{-x^2/2}}{\sqrt{2\pi}},
$$

$$
N(x)\approx
1-\phi(x)t
\left(
0.319381530
-0.356563782t
+1.781477937t^2
-1.821255978t^3
+1.330274429t^4
\right)
$$

pour \(x\geq0\), puis \(N(x)=1-N(-x)\) pour \(x<0\). L’erreur annoncée
par le module est inférieure au basis point pour cet usage de contrôle.

La volatilité initiale du run est globale (`35 %` par défaut). Les IV propres à
chaque jambe restent utilisées par les scénarios V10.1, mais pas comme variance
initiale distincte de chaque jambe dans le Monte-Carlo V11.

## 13. Règles de sortie simulées

Chaque trajectoire est parcourue dans cet ordre :

1. profit complet si \(P\&L_t\geq1.50C\) ;
2. stop opérationnel si \(P\&L_t\leq-0.70C\) ;
3. après un pic supérieur ou égal à \(0.80C\), revue trailing si la baisse
   depuis ce pic atteint \(0.30C\) ;
4. revue IV crush si l’IV a baissé d’au moins 35 % par rapport à l’entrée ;
5. sortie temps à 60 jours ou moins de l’échéance ;
6. sinon sortie à l’horizon simulé.

Les seuils sont configurables. Dans le moteur de trajectoires, une « revue »
est modélisée comme une sortie pour mesurer la distribution conditionnelle. En
opération réelle, elle reste une décision humaine.

## 14. Métriques Monte-Carlo

Pour les P&L réalisés simulés \(X_1,\ldots,X_N\) :

$$
E[X]=\frac{1}{N}\sum_iX_i,
\qquad
Median(X)=Q_{50\%}(X).
$$

$$
P(profit)=\frac{1}{N}\sum_i\mathbf{1}_{X_i>0}.
$$

La « perte totale » est approchée par une perte d’au moins 95 % de la mise :

$$
P(perte\ totale)=
\frac{1}{N}
\sum_i\mathbf{1}_{X_i\leq-0.95C}.
$$

$$
P(\times2)=P(X\geq C),
$$

$$
P(\times3)=P(X\geq2C),
\qquad
P(\times5)=P(X\geq4C).
$$

Avec \(q_{0.05}=Q_{5\%}(X)\) :

$$
VaR_{95}=\max(0,-q_{0.05}),
$$

$$
CVaR_{95}=
\max\left(
0,
-E[X\mid X\leq q_{0.05}]
\right).
$$

Les trajectoires raisonnables basse et haute sont \(Q_{5\%}\) et \(Q_{95\%}\).

Le drawdown d’une trajectoire de valeur \(V_t\) est :

$$
DD_{path}=
\max_t\left(
\max_{u\leq t}V_u-V_t
\right).
$$

Le rapport conserve le maximum de ce drawdown sur les trajectoires, le premier
jour profitable moyen, la probabilité de sortie avant l’horizon et le comptage
des motifs de sortie.

## 15. Robustesse multi-modèles

Soit \(K\) les 16 couples modèle/régime :

$$
ProfitableFraction=
\frac{1}{|K|}
\sum_{k\in K}
\mathbf{1}_{E[X_k]>0}.
$$

La dispersion neutre est :

$$
D_{neutral}=
\max_{k\in neutral}E[X_k]
-\min_{k\in neutral}E[X_k].
$$

Avec :

$$
p_D=\min(D_{neutral}/C,1),
$$

$$
p_A=\min(
\max_{k\in\{adverse,rupture\}}CVaR_{95,k}/C,
1
),
$$

le score de robustesse est :

$$
Robustesse=
100\max\left[
0,
0.65\,ProfitableFraction
+0.20(1-p_D)
+0.15(1-p_A)
\right].
$$

Des flags sont ajoutés si :

- moins de la moitié des couples ont une espérance positive ;
- la dispersion neutre dépasse 50 % du coût ;
- la CVaR adverse dépasse 80 % du coût.

Ce score est un résumé diagnostique, pas une gate de promotion autonome.

## 16. Pondération des modèles et régimes

Les probabilités bayésiennes sont regroupées par régime :

$$
\pi_r=
\sum_{s:mapping(s)=r}P(s\mid événements).
$$

Dans chaque régime, le poids est partagé également entre les modèles
disponibles :

$$
w_{r,m}=
\frac{\pi_r}{N_{models,r}}.
$$

Les champs `probability` des régimes dans la configuration garantissent une
distribution déclarée cohérente, mais l’optimiseur utilise les poids
\(\pi_r\) issus du posterior bayésien.

## 17. Optimisation entière sous contraintes

Pour une allocation entière \(x=(x_1,\ldots,x_n)\), le P&L d’un groupe
modèle/régime \(k\) est :

$$
X_k(x)=\sum_ix_iX_{i,k}.
$$

Son espérance agrégée est :

$$
\mu(x)=\sum_kw_kE[X_k(x)].
$$

La variance combine variance intra-groupe et dispersion inter-groupes :

$$
Var(x)=
\sum_kw_k\left[
Var(X_k(x))
+(E[X_k(x)]-\mu(x))^2
\right].
$$

La CVaR d’allocation est la pire CVaR parmi les groupes adverse et rupture :

$$
CVaR^{stress}(x)=
\max_{k\in\{adverse,rupture\}}
CVaR_{95}(X_k(x)).
$$

Le risque d’exécution est :

$$
ExecutionRisk(x)=
\sum_ix_i\,spreadMax_i\,C_i.
$$

La dispersion modèle est :

$$
ModelDispersion(x)=
\max_kE[X_k(x)]-\min_kE[X_k(x)].
$$

La fonction objectif exacte utilisée pour classer les allocations est :

$$
J(x)=
\frac{\mu(x)}{B_{USD}}
-\lambda\frac{Var(x)}{B_{USD}^2}
-\gamma\frac{CVaR^{stress}(x)}{B_{USD}}
-\eta\frac{ExecutionRisk(x)}{B_{USD}}
-\zeta\frac{ModelDispersion(x)}{B_{USD}}.
$$

Contraintes :

$$
x_i\in\mathbb{N}_0,
$$

$$
\sum_ix_iCost_i^{EUR}\leq B_{EUR},
$$

$$
\sum_ix_iMaxLoss_i^{EUR}\leq MaxLoss_{EUR},
$$

$$
\sum_ix_iContracts_i\leq MaxContracts,
$$

avec structure à débit borné et gate de liquidité V10.1 satisfaite.

L’ensemble réalisable est fini et entièrement énuméré. Le moteur ne résout pas
une relaxation continue puis n’arrondit pas : chaque résultat publié est
directement faisable en contrats entiers sous les hypothèses du rapport.

Coefficients livrés :

| Profil | \(\lambda\) variance | \(\gamma\) CVaR | \(\eta\) exécution | \(\zeta\) dispersion |
| --- | ---: | ---: | ---: | ---: |
| prudent | 1,20 | 1,00 | 0,80 | 0,80 |
| balanced | 0,65 | 0,65 | 0,45 | 0,50 |
| aggressive | 0,25 | 0,30 | 0,25 | 0,25 |

L’allocation nulle \(x=0\) représente cash/`NO_TRADE` :

$$
J(0)=0,
\qquad
CashReserve=B_{EUR}.
$$

Elle est toujours évaluée et conservée dans les résultats lorsque la taille du
Top N le permet. Le budget total n’est jamais forcé.

### Gradient et Hessienne

Pour le diagnostic lisse moyenne-variance seulement :

$$
J_{MV}(x)=
\frac{\mu^\top x}{B}
-\lambda\frac{x^\top\Sigma x}{B^2}.
$$

$$
\nabla J_{MV}(x)=
\frac{\mu}{B}
-\frac{2\lambda\Sigma x}{B^2},
$$

$$
\nabla^2J_{MV}=
-\frac{2\lambda\Sigma}{B^2}.
$$

Les valeurs propres de la Hessienne indiquent si cette composante quadratique
est concave. Ces diagnostics n’incluent ni CVaR, ni pénalité d’exécution, ni
dispersion, ni contraintes entières. La décision finale vient toujours de
l’énumération exacte.

## 18. Stress et gates de promotion

Le coût de spread agrégé d’un candidat est :

$$
SpreadCost=
\sum_i(ask_i-bid_i)q_iM_i.
$$

Avec :

$$
Baseline=
\min_{m\in modèles}
E[P\&L_{neutral,m}],
$$

les stress implémentés sont :

$$
Stress_{spread\times1.5}=
Baseline-0.5\,SpreadCost,
$$

$$
Stress_{slippage\times2}=
Baseline-Slippage_{initial},
$$

$$
Stress_{fees\times2}=
Baseline-Fees_{initial}.
$$

Le moteur conserve aussi :

$$
\min_mE[P\&L_{adverse,m}],
\qquad
\min_mE[P\&L_{rupture,m}],
$$

et la pire CVaR adverse/rupture.

Le stress passe uniquement si :

$$
\min(
Stress_{spread},
Stress_{slippage},
Stress_{fees},
E_{adverse}^{worst},
E_{rupture}^{worst}
)>0,
$$

et :

$$
CVaR_{stress}^{worst}\leq0.80C.
$$

Même si ce stress passe, V11 impose actuellement :

```text
promotion_eligible=false
```

car :

- les holdouts V7–V9 ont déjà été inspectés et sont contaminés ;
- le contrat walk-forward et le holdout verrouillé existent, mais aucun dataset
  historique réel autorisé ne les a encore validés ;
- le paper monitoring n’a pas été exécuté.

V11.1 ajoute aussi une suite de stress déterministe : retard de catalyseur,
IV crush, sell-off, taux, EUR/USD, bid/ask ×2, dégradation OI/volume, gaps,
midpoint indisponible, liquidation prudente, slippage ×2, frais ×2 et sortie
anticipée. Lorsqu’un historique requis n’existe pas, le stress porte
`data_insufficient` avec sa méthode, ses hypothèses et son blocker ; il
n’invente pas de P&L.

## 19. Posture du rapport

La posture suit cet ordre :

```text
aucun candidat
  -> blocked

tous les rangs 1 sont NO_TRADE
  -> no_trade

sinon, données requises manquantes
ou source synthétique
ou toutes les previews bloquées
  -> watchlist

sinon
  -> paper_review
```

`paper_review` ne signifie toujours pas « prêt à trader ». Il signifie que les
blocages de données immédiats sont levés et que la validation paper peut
commencer.

## 20. Surveillance d’une position

Le dossier initial conserve :

- distribution de scénarios ;
- spot, IV, taux et Greeks ;
- catalyseurs et invalidations ;
- prix d’entrée, coût réel et slippage ;
- régime initial ;
- plan de sortie ;
- acteur humain responsable.

Les variations sont :

$$
\Delta S=S_{current}-S_0,
\qquad
\Delta IV=IV_{current}-IV_0,
\qquad
\Delta r=r_{current}-r_0.
$$

L’attribution locale utilise les Greeks initiaux :

$$
P\&L_\Delta=\Delta_0\Delta S,
$$

$$
P\&L_\Gamma=
\frac{1}{2}\Gamma_0(\Delta S)^2,
$$

$$
P\&L_\Theta=\Theta_0\times\text{jours écoulés},
$$

$$
P\&L_{Vega}=Vega_0\times\Delta IV\times100,
$$

$$
P\&L_{Rho}=Rho_0\times\Delta r\times100.
$$

Les P&L comptables du snapshot sont :

$$
P\&L_{\text{latent}}=
\text{Valeur de marché}-\text{coût réel},
$$

$$
P\&L_{\text{total}}=
P\&L_{\text{latent}}+P\&L_{\text{réalisé}},
$$

$$
ROC=\frac{P\&L_{\text{total}}}{\text{coût réel}}.
$$

Le changement de probabilité d’un scénario est :

$$
\Delta p_s=p_{s,current}-p_{s,initial}.
$$

Les règles peuvent déclencher invalidation fondamentale, données insuffisantes
ou périmées, stop prudent, sortie temporelle, objectif complet ou partiel,
IV crush, liquidité détériorée, espérance restante négative et dépassement
CVaR. L’action finale suit la priorité :

```text
HOLD < WATCH < REDUCE < EXIT_REVIEW < DATA_STALE
     < BLOCKED_INSUFFICIENT_DATA < THESIS_INVALIDATED
```

Une baisse d’au moins 20 points d’un scénario ou un changement de régime
transforme aussi `HOLD` en `WATCH`. Chaque trigger conserve valeur observée,
seuil, date, sévérité, action suggérée, données requises et confiance.

La divergence thèse/marché est classée :

```text
thesis_weaker_than_market
  si min(Δp) < -10 points et P&L total >= 0

market_weaker_than_thesis
  si min(Δp) >= 0 et P&L total < 0

aligned_or_inconclusive
  sinon
```

L’impact d’exécution courant est conservé comme diagnostic séparé. Cette
attribution de premier/deuxième ordre ne doit pas être confondue avec une
réconciliation exacte du P&L.

La commande :

```bash
ttwo-options position assess \
  --dossier <DOSSIER_INITIAL.json> \
  --current <SNAPSHOT_ACTUEL.json> \
  --output reports/v11/position_monitor.json

ttwo-options position replay \
  --trajectory fixtures/v11/position_trajectory.example.json \
  --output reports/v11/position_trajectory.json
```

La première commande évalue un snapshot fourni ; la seconde rejoue la fixture
chronologique par le même moteur. Il n’existe pas encore de daemon, de polling
continu ou de suivi automatique des états d’ordres.

## 21. Ce qui est réellement relié dans V11

| Composant | Statut |
| --- | --- |
| V10.1 → sélection du pool V11 | utilisé |
| Bayes → poids des quatre régimes | utilisé |
| Dupire → nœuds du modèle local-vol | utilisé |
| 4 modèles × 4 régimes → valorisation | utilisé |
| règles de sortie → P&L simulés | utilisé |
| P&L multi-modèles → allocation entière | utilisé |
| stress/holdout/paper → promotion | utilisé, promotion forcée à `false` |
| observations → règles déterministes → événements | utilisé avec preuve et revue |
| événements approuvés → Bayes | utilisé ; pending/rejected/expired ignorés |
| calibration historique | interface utilisée ; données réelles absentes |
| walk-forward | interface utilisée ; fixture non validante |
| covariance factorielle → SDE | diagnostic seulement |
| combo quotes IBKR → previews | utilisé si connecteur injecté par code |
| connecteurs live → CLI par défaut | non configurés |
| position monitor → broker | advisory-only, aucune mutation |

Cette table est importante : la présence d’un module ne signifie pas qu’il
contrôle déjà une décision en aval.

## 22. Hypothèses, faits, inférences et décisions

### Faits logiciels

- V10.1 construit calls, bull spreads et butterflies sur des contrats listés.
- V11 exécute 16 couples modèle/régime par candidat.
- Les contraintes entières, le cash et `NO_TRADE` sont évalués explicitement.
- Les rapports conservent provenance, paramètres, warnings, métriques et
  blockers.
- La frontière d’ordre est interdite par contrat et par tests.

### Hypothèses à tester

- priors et likelihoods bayésiens ;
- drifts et paramètres de saut ;
- paramètres Heston ;
- taux, dividende et FX configurés ;
- surface locale extraite d’une chaîne synthétique ou partielle ;
- coefficients des trois profils ;
- seuils de sortie et de stress ;
- approximation Black-Scholes conditionnelle des trajectoires.

### Inférences autorisées

- comparer la sensibilité de structures sous les mêmes hypothèses ;
- détecter qu’une structure est fragile à certains modèles ou coûts ;
- conserver cash si son objectif domine les allocations ;
- préparer une watchlist ou un plan de paper validation.

### Décisions interdites sans validation supplémentaire

- considérer un posterior comme une probabilité vraie de GTA VI ;
- considérer un P&L attendu comme un rendement promis ;
- transformer un score ou un rang en recommandation ;
- réutiliser un holdout contaminé pour promouvoir une stratégie ;
- présenter une quote jambe par jambe comme un fill combo ;
- envoyer, modifier, annuler ou exercer un ordre.

## 23. Paramètres par défaut et reproductibilité

Les paramètres sont versionnés dans :

- `configs/thesis_scanner/default.yaml` pour V10.1 ;
- `configs/intelligence/v11.yaml` pour V11.

Le profil `fast_fixture` V11 de démonstration utilise notamment :

```text
paths=1000
steps=90
horizon_days=180
seed=20260728
budget_eur=1000
maximum_loss_eur=1000
maximum_contracts=4
candidate_pool_size=6
```

Une identité stable est calculée à partir des inputs principaux. Les seeds
séparent les modèles et régimes. Un même jeu d’inputs et une même date de
création injectée dans les tests donnent les mêmes trajectoires et résultats.
Le manifeste conserve `run_id`, hash de configuration, hash de données, hash
d’inputs, versions, durées par étape, mémoire mesurée, cache déterministe et
statut de reprise. Les profils autorisés sont `fast_fixture`, `research`,
`validation` et `exhaustive` ; aucun profil `production_live` n’existe.

## 24. Validation logicielle

La livraison V11 est contrôlée par :

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/validate_research_registry.py
.venv/bin/python scripts/phase10_release_audit.py --check
.venv/bin/python scripts/security_gate.py
.venv/bin/pip check
```

La validation actuelle couvre :

- schémas et policies ;
- cutoff, fraîcheur, unités, provenance, doublons et contradictions ;
- Bayes, waterfall, caps, sensibilités et probabilités valides ;
- covariance PSD ;
- reproductibilité, convergence et diagnostics des quatre modèles ;
- Dupire, arbitrage, Heston, sauts et fallbacks ;
- métriques, stress et règles de sortie ;
- allocation entière, concentration, Greeks, cash et `NO_TRADE` ;
- connecteurs point-in-time mockés ;
- calibration et walk-forward fail-closed sans look-ahead ;
- rejet des adaptateurs capables d’ordonner ;
- monitoring, invalidation et replay multi-date ;
- property tests, pipeline, rapports autonomes et schémas exportés ;
- scan de secrets et frontière globale d’exécution.

Le workflow `.github/workflows/offline-validation.yml` exécute ces contrôles et
génère les rapports fixtures sans connexion live.

Cette validation prouve le comportement du logiciel sur les cas testés. Elle
ne valide pas une stratégie TTWO.

## 25. Limites de recherche

- La fixture V10.1 livrée est synthétique.
- Les priors, likelihoods, paramètres de régime et scores sont
  `calibration_required`.
- La surface Dupire n’est pas une calibration globale sans arbitrage.
- Le repricer Monte-Carlo est européen/conditionnel entre les contrôles
  américains V10.1.
- Le facteur de covariance livré par défaut ne contient que TTWO.
- Le calendrier de marché requis n’est pas configuré dans le run offline.
- Les connecteurs SEC/FRED/RSS/Trends/IBKR ne sont pas appelés par défaut.
- Google Trends API reste un accès alpha limité.
- Les droits OPRA, `conId`, livrables, combo quotes, commissions et marge
  restent à vérifier.
- Les holdouts V7–V9 sont contaminés.
- Le framework de holdout/walk-forward existe, mais aucun résultat réel
  autorisé ni paper trading n’est terminé.
- Le suivi de position est un calcul sur snapshot, pas une surveillance
  autonome.

## 26. Références méthodologiques

- Cox, Ross et Rubinstein, modèle binomial et exercice anticipé ;
- Merton, diffusion avec sauts ;
- Heston, volatilité stochastique ;
- Dupire, volatilité locale ;
- QuantLib, moteur finite-difference américain ;
- OCC, risques contractuels des options ;
- IBKR TWS API et abonnements de marché ;
- OPRA pour les données consolidées options ;
- SEC EDGAR, FRED, Take-Two RSS et Google Trends pour les données externes.

Les liens primaires et limites d’intégration sont détaillés dans
[`docs/architecture/V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md`](docs/architecture/V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md).

## Données live IBKR/OPRA — frontière V11

- OPRA est le flux de données temps réel des options américaines ; OPRA
  n’exécute aucun ordre.
- Le port V11 sait recevoir des cotations options et combo en lecture seule via
  un adaptateur TWS/IB Gateway injecté. Le dépôt n’embarque ni session IBKR
  configurée, ni identifiant, ni abonnement de marché.
- Les quotes combo IBKR doivent valider les spreads et butterflies, car une
  construction bid/ask jambe par jambe ne prouve pas un prix combo exécutable.
- Les droits de marché, abonnements, `conId`, livrables, commissions et marges
  du compte IBKR restent à vérifier sur une session réelle.
- Les secrets et identifiants resteront exclusivement dans l’environnement et
  ne devront jamais être enregistrés dans le dépôt, les fixtures ou les
  rapports.
- Le mode fixture/offline restera disponible pour les tests reproductibles.
- Une donnée périmée devra bloquer la création d’un ticket exploitable.
- Une éventuelle exécution automatique constituerait un projet distinct,
  nécessitant une validation explicite et de nouveaux garde-fous.
- Tous les tickets restent des previews avec
  confirmation humaine, `transmit=false`, `what_if=true` et
  `order_capability=forbidden`.

Checklist de livraison :

- [x] Stabiliser les calculs contractuels et les scénarios Python.
- [x] Stabiliser le dashboard autonome, Top N et les tests d’accessibilité.
- [x] Implémenter une frontière IBKR/OPRA étroite, injectée et lecture seule.
- [ ] Exécuter une campagne source-backed sur session IBKR/OPRA autorisée et
  valider fraîcheur, droits, contrats, quotes combo, commissions et marges.
