# Matrice de readiness — peut-on construire les stratégies ?

Date : 2026-07-06
Statut : `draft_to_validate`

## Réponse courte

Oui, on a assez pour construire la **spécification de recherche** et un futur **scanner IBKR en
lecture seule**.

Non, on n'a pas encore assez pour activer des décisions de trading. Il manque la validation
quantitative, les données live, les coûts réels, la conformité broker et les règles de contrôle
humain.

## État par famille de stratégie

Cette matrice répond à deux questions différentes :

1. peut-on écrire la **spécification logique** de la stratégie à partir du corpus ?
2. peut-on l'utiliser en conditions réelles ?

Pour l'instant, la réponse 1 est souvent oui. La réponse 2 reste non tant que les contrôles live,
broker, marge, liquidité et validation humaine ne sont pas en place.

| Famille | Corpus suffisant ? | Ce qu'on peut déjà spécifier | Ce qui manque avant usage réel | Statut futur outil |
|---|---|---|---|---|
| Achat call/put directionnel | `oui_pour_spec` | McMillan : choix strike/horizon/delta ; Mauboussin/Lynch/Klarman : thèse sous-jacent, marge de sécurité et scénarios. | Distribution prix/temps, IV actuelle vs historique, liquidité, sizing, invalidation, catalyseur, comparaison action vs option vs vertical spread. | `research_candidate_only` |
| Bull/bear vertical spreads | `oui_pour_spec` | McMillan/Natenberg : payoff, break-even, max gain/perte, agressivité, coûts, effet des strikes. | Bid/ask réels par jambe, net debit/credit exécutable, assignment, early exercise, ex-dividend, marge, commissions, exécution multi-leg. | `spread_candidate_requires_live_quotes` |
| Calendar / time spreads | `oui_pour_spec` | McMillan/Natenberg : theta, term structure, sensibilité IV/temps, logique near-term vs long-term. | Surface IV live, événements, earnings, ex-dividend, assignment sur jambe courte, modèle American si equity, règle de roll/close. | `term_structure_candidate_requires_event_check` |
| Butterfly / condor | `oui_pour_spec` | McMillan/Natenberg : payoff borné, coûts multi-jambes, zone de profit, neutralité relative. | Slippage multi-leg, commissions, probabilité de finir dans la zone, pin risk, assignment, open interest suffisant, close/roll rules. | `defined_risk_candidate_requires_execution_check` |
| Ratio spreads / backspreads | `partiel_to_review` | Natenberg/McMillan : logique convexité, crédit, risque asymétrique, exposition gamma/vega. | Encadrement strict du risque non borné, marge, gap stress, max size, permissions broker, stop rules, validation humaine obligatoire. | `unbounded_risk_to_review` |
| Straddle / strangle | `oui_pour_spec` | Natenberg/Passarelli : long/short vol, gamma/theta, IV/RV, logique d'événement et de mouvement. | Gestion des gaps, earnings, hedge policy, stop rules, coûts, IV crush, marge pour short vol, blacklist/event mode. | `short_gamma_or_event_mode_required` |
| Gamma scalping | `oui_pour_spec_pas_live` | Passarelli/Natenberg : long/short gamma, theta, realized vol, hedge deltas, P&L gamma vs theta. | Données intraday fiables, frais, slippage, fréquence hedge, backtest, paper trading, latence, logs de hedge, attribution P&L. | `paper_only_until_backtested` |
| Protective put/call, covered write, fence/collar | `oui_pour_spec` | Natenberg ch. 13 : hedging, insurance, synthetics, collars/fences, coût vs protection. | Besoin réel de couverture, portefeuille exact, fiscalité, assignment, borrow, dividendes, produit exact, coût maximal accepté. | `hedge_candidate_requires_portfolio_context` |
| LEAPS / substitution action | `oui_pour_spec` | McMillan ch. 25 : duration, delta, decay, leverage, substitution partielle à l'action. | Dividendes, borrow, liquidité long-dated, surface IV longue, spread souvent large, delta drift, plan de roll/sortie. | `long_dated_candidate_requires_liquidity_check` |
| Overlay value / expectations | `oui_pour_research` | Mauboussin : reverse DCF, scénarios, attentes implicites, comparaison prix vs valeur. | Données fondamentales actuelles, filings, WACC, comparables, probabilités validées, lien explicite entre thèse fondamentale et structure option. | `valuation_overlay_only` |

## Checklist de complétion par famille

### Achat call/put directionnel

À ajouter avant tout scoring réel :

- thèse sous-jacent structurée : catalyseur, horizon, scénario central, scénario adverse,
  invalidation ;
- IV actuelle comparée à IV historique, realized volatility et événements à venir ;
- liquidité minimale : bid/ask, volume, open interest, profondeur ;
- sizing par perte maximale, pas par conviction ;
- comparaison obligatoire avec achat action, no-trade et vertical spread.

Statut si incomplet : `thesis_or_data_incomplete`.

### Bull/bear vertical spreads

À ajouter avant tout scoring réel :

- prix bid/ask live de chaque jambe et prix net réaliste ;
- maximum gain, maximum loss, break-even, rendement sur risque, probabilité implicite ;
- test ex-dividend et early assignment si equity américaine ;
- marge pré-trade et commissions réelles ;
- règle de sortie : take-profit, stop, expiration, roll ou close.

Statut si incomplet : `live_quotes_or_margin_missing`.

### Calendar / time spreads

À ajouter avant tout scoring réel :

- term structure IV par échéance et par strike ;
- événement entre les deux expirations : earnings, macro, dividende, décision réglementaire ;
- risque d'assignment sur la jambe courte ;
- modèle compatible avec options américaines si nécessaire ;
- règle de fermeture avant expiration courte.

Statut si incomplet : `term_structure_or_event_incomplete`.

### Butterfly / condor

À ajouter avant tout scoring réel :

- slippage multi-jambes et capacité réelle à entrer/sortir ;
- probabilité que le sous-jacent finisse dans la zone de profit ;
- risque de pin et assignment autour des strikes ;
- commissions par jambe ;
- règle de fermeture avant expiration si le centre est proche.

Statut si incomplet : `execution_quality_incomplete`.

### Ratio spreads / backspreads

À ajouter avant tout scoring réel :

- stress test sur gros gap, volatilité et expiration ;
- preuve que le risque maximum est borné ou explicitement accepté ;
- marge broker pré-trade ;
- limite de taille stricte ;
- validation humaine obligatoire avant tout passage de `candidate` à `trade_ready`.

Statut si incomplet : `unbounded_risk_to_review`.

### Straddle / strangle

À ajouter avant tout scoring réel :

- distinction claire entre long vol et short vol ;
- IV/RV, IV rank, skew, term structure, événement ;
- règle earnings : interdit, autorisé, ou mode spécial ;
- hedge policy : quand couvrir delta, combien, avec quel coût ;
- stress gap et scénario IV crush.

Statut si incomplet : `event_and_gap_risk_incomplete`.

### Gamma scalping

À ajouter avant tout scoring réel :

- données intraday fiables et horodatées ;
- règle de hedge : seuil delta, intervalle temps, bande de prix ou volatilité ;
- frais, slippage, spread et impact de marché ;
- attribution P&L : gamma scalp, theta, vega, coûts ;
- backtest puis paper trading avant toute exécution.

Statut si incomplet : `paper_only_until_backtested`.

### Protective put/call, covered write, fence/collar

À ajouter avant tout scoring réel :

- exposition réelle à couvrir : taille, horizon, devise, contrainte de perte ;
- objectif : assurance catastrophe, revenu, réduction de volatilité, collar à coût réduit ;
- fiscalité, borrow, dividendes, assignment ;
- coût maximal de protection accepté ;
- comparaison avec futures, cash reduction, no-hedge et spread de couverture.

Statut si incomplet : `hedge_objective_incomplete`.

### LEAPS / substitution action

À ajouter avant tout scoring réel :

- liquidité long-dated et spread bid/ask ;
- dividendes attendus, taux, borrow, corporate actions ;
- delta, vega, theta et convexité dans le temps ;
- comparaison avec achat action financé, call court, vertical long-dated ;
- plan de roll avant perte de liquidité ou accélération du theta.

Statut si incomplet : `long_dated_data_incomplete`.

### Overlay value / expectations

À ajouter avant tout usage comme input de stratégie option :

- reverse DCF ou scénario d'attentes implicites documenté ;
- filings récents : 10-K, 10-Q, 8-K, investor presentation si pertinent ;
- WACC, croissance, marge, buybacks, SBC, dette, dilution ;
- probabilités explicites par scénario ;
- traduction séparée vers options : horizon, IV, liquidité, structure adaptée.

Statut si incomplet : `fundamental_thesis_to_review`.

## Statuts de blocage standard

Le futur outil doit pouvoir expliquer pourquoi une stratégie n'est pas éligible. Statuts proposés :

- `data_incomplete` : données contrat, marché ou historique insuffisantes ;
- `live_quotes_missing` : bid/ask ou chain options non disponibles ;
- `liquidity_veto` : spread trop large, open interest/volume trop faible ;
- `margin_unknown` : marge ou permissions broker non vérifiées ;
- `corporate_action_to_review` : contrat ajusté, split, merger, special dividend ou deliverable non standard ;
- `unbounded_risk_to_review` : risque théoriquement non borné ou stress test insuffisant ;
- `event_risk_to_review` : earnings, dividend, regulatory event ou macro event non traité ;
- `thesis_to_review` : thèse sous-jacent ou scénario non validé ;
- `backtest_required` : stratégie nécessitant historique/paper trading avant usage ;
- `human_validation_required` : décision ou stratégie sensible nécessitant validation explicite.

## Contrat minimal de données

Le futur outil doit refuser de scorer une stratégie si ces données manquent :

- chaîne options complète : bid, ask, strike, expiration, type, volume, open interest,
  horodatage ;
- identifiants broker : `conId`, `localSymbol`, `tradingClass`, exchange, currency ;
- multiplicateur, deliverable, style d'exercice, settlement, corporate-action adjustment ;
- sous-jacent : prix live, historique, borrow si short, dividendes, événements ;
- IV par jambe, modèle Greeks, delta/gamma/theta/vega/rho ;
- realized volatility à plusieurs horizons ;
- surface IV : skew, term structure, IV rank/percentile si disponible ;
- taux risk-free par maturité/devise ;
- commissions, exchange fees, slippage estimé, marge ;
- permissions compte : options level, short stock, margin type, product restrictions ;
- positions existantes et risque marginal portefeuille ;
- scénario prix/temps/IV + condition d'invalidation ;
- journal de décision et statut de validation.

## Règles non négociables du futur moteur

1. Une règle de livre ne peut pas devenir ordre.
2. Une stratégie doit toujours être comparée à une alternative plus simple : no-trade, action,
   option nue, spread.
3. Les Greeks doivent être mesurés au niveau portefeuille, pas seulement option isolée.
4. L'edge doit être net des coûts, slippage, marge, taxes pertinentes et risque d'exécution.
5. La liquidité et le bid/ask peuvent veto une stratégie théoriquement attractive.
6. Les probabilités de scénarios doivent rester visibles et contestables.
7. Toute stratégie short gamma ou à risque non borné doit avoir un stress test explicite.
8. Le mode initial IBKR doit être `read_only` / `paper` jusqu'à validation humaine.

## Verdict de construction

Prochaine étape raisonnable :

```text
1. Spécifier le contrat de données IBKR.
2. Construire un moteur read-only de scoring et explication.
3. Backtester les familles une par une.
4. Paper-trader.
5. Seulement ensuite discuter d'ordres préparés.
```

Ce repo est prêt pour l'étape 1. Il n'est pas prêt pour exécution.

## Cas appliqué : TTWO / GTA VI

Le document `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md` applique cette matrice au cas Take-Two /
Grand Theft Auto VI.

Statut :

- `research_spec_ready` pour construire un collecteur et scorer en lecture seule ;
- `trade_not_ready` tant que la chaîne options TTWO live, la surface IV, la liquidité, les marges,
  les commissions, les scénarios de retard et les règles de sortie ne sont pas calculés ;
- `human_validation_required` pour toute structure short gamma, ratio/backspread ou risque non borné.
