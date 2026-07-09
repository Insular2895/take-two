---
title: "Clean usable ruleset 2026 — TTWO / GTA VI options research engine"
date: 2026-07-09
status: draft_to_validate
scope: research_engine_spec
decision_status: not_trade_recommendation
execution_mode: read_only_or_paper_only
---

# Clean usable ruleset 2026 — TTWO / GTA VI options research engine

Ce fichier est la version propre de la mine documentaire.

Objectif : garder uniquement les règles utiles pour concevoir le futur outil, supprimer le bruit, et
remplacer les informations périmées par des sources 2026 ou par des données live obligatoires.

## Verdict opérationnel

On a assez de connaissance pour construire un moteur de recherche/scoring **read-only** :

- comparer action, option nue, vertical spread, calendar, butterfly/condor, straddle/strangle,
  collar/fence, LEAPS et no-trade ;
- expliquer le risque par Greeks, payoff, IV/RV, liquidité, coûts, marge et scénario fondamental ;
- bloquer les stratégies lorsque les données live, broker ou fondamentales manquent.

On n'a pas assez pour recommander ou exécuter un trade réel. Le moteur doit rester `read_only` ou
`paper_only` tant que la chaîne options, les coûts, la marge, les événements et la validation humaine
ne sont pas présents.

```text
Livre = architecture logique.
Source 2026 = règle actuelle / donnée réglementaire.
Broker + marché live = vérité opérationnelle.
Humain = validation finale.
```

## Ce qui est supprimé du corpus opérationnel

Les 365 blocs bruts ne sont pas détruits physiquement : ils restent une mine `to_review`. En revanche,
ils sont exclus du corpus utilisable tant qu'ils n'ont pas été nettoyés.

Sont exclus du moteur :

1. les exemples de prix, taux ou commissions anciens utilisés comme paramètres actuels ;
2. les règles sans condition/action claire ;
3. les doublons qui répètent un payoff sans ajouter de contrainte ;
4. les conseils psychologiques non transformés en garde-fou observable ;
5. les tableaux OCR non vérifiés visuellement lorsqu'ils servent à un calcul quantitatif ;
6. les règles qui supposent `contrat = 100 actions` sans vérifier le multiplicateur/deliverable ;
7. les affirmations “IV haute = vendre / IV basse = acheter” sans événement, coûts, skew,
   liquidité, sizing et scénario adverse ;
8. les références réglementaires anciennes sur settlement, short sale, assignment, marge ou fiscalité ;
9. les règles qui confondent thèse fondamentale et signal optionnel ;
10. toute règle qui produit un ordre sans données live et validation humaine.

## Contrat de promotion

Une information passe dans le futur outil seulement si elle suit cette chaîne :

```text
raw_block
→ candidate_documentary
→ clean_rule
→ testable_rule
→ read_only_gate
→ active_after_human_validation
```

Dans l'état actuel, les règles ci-dessous sont `clean_rule` ou `read_only_gate`. Aucune n'est
`active_after_human_validation`.

## Règles propres par domaine

### A. Données contrat et actualité 2026

| ID | Règle propre | Source actuelle | Action outil |
|---|---|---|---|
| CUR-001 | Ne jamais utiliser un cycle de règlement tiré d'un livre ancien. | SEC / OCC, T+1 depuis 2024-05-28. | Exiger `settlement_cycle`; bloquer cash-flow si absent. |
| CUR-002 | Ne jamais supposer l'exercice/assignment automatique sans règles OCC + broker. | OCC ODD actuel + broker. | Exiger `exercise_style`, expiration, ex-dividend, assignment risk. |
| CUR-003 | Ne jamais hard-coder `contracts × 100`. | OCC specs + IBKR contract details. | Exiger `multiplier`, `deliverable`, `conId`, `localSymbol`, `adjusted_contract`. |
| CUR-004 | Les anciennes règles d'uptick ne valent pas comme règle actuelle. | SEC Reg SHO Rule 201. | Vérifier shortable, locate, borrow, SSR/Rule 201 avant short stock hedge. |
| CUR-005 | Le taux sans risque doit être par maturité/devise, pas un taux fixe global. | U.S. Treasury / broker curve. | Mapper chaque expiration à un taux vérifié. |
| CUR-006 | Les dividendes et corporate actions sont des inputs de risque, pas des notes annexes. | SEC filings, OCC adjustments, broker. | Exiger ex-date/pay-date/special dividends/splits avant options US equity. |
| CUR-007 | Les coûts ne sont pas constants : commissions, exchange fees, slippage, borrow et marge dépendent du compte. | IBKR pricing/margin. | Pré-trade cost/margin check obligatoire en paper/read-only. |
| CUR-008 | Les fondamentaux doivent venir des filings actuels, pas d'exemples de livres. | SEC EDGAR / company filings. | Récupérer 10-K, 10-Q, 8-K, guidance, dette, SBC, buybacks. |

### B. Mathématiques et pricing

| ID | Règle propre | Base documentaire | Action outil |
|---|---|---|---|
| MATH-001 | Tout payoff doit être calculé par jambe puis agrégé au niveau stratégie. | McMillan / Natenberg. | Générer payoff, max loss, max gain, breakevens, scénarios. |
| MATH-002 | Les Greeks sont locaux : ils doivent être recalculés à chaque variation de prix, temps ou IV. | Natenberg / Passarelli. | Reprice par grille prix/temps/IV ; ne pas figer le delta. |
| MATH-003 | Les Greeks doivent être agrégés au niveau portefeuille, pas seulement contrat isolé. | Natenberg / Grinold-Kahn. | `portfolio_delta/gamma/theta/vega/rho` obligatoires. |
| MATH-004 | L'edge théorique n'est pas un edge réel tant qu'il n'est pas net de coûts et contraintes. | Natenberg / Grinold-Kahn. | Afficher edge brut, coûts, edge net, edge net stressé. |
| MATH-005 | Long gamma gagne par mouvement/rebalancement seulement si le gain couvre theta + coûts. | Passarelli / Natenberg. | P&L attribution : gamma scalp, theta, vega, fees, slippage. |
| MATH-006 | Short gamma encaisse theta mais vend une assurance contre gaps et accélérations de delta. | Passarelli / Natenberg. | Stress gap obligatoire ; statut `short_gamma_event_mode`. |
| MATH-007 | IV/RV est une comparaison, pas un signal seul. | Passarelli / Natenberg. | Ajouter événement, skew, term structure, coût et régime de marché. |
| MATH-008 | Une probabilité implicite ou historique doit être liée à un horizon. | Natenberg / Mauboussin. | Refuser un score sans horizon prix/temps explicite. |
| MATH-009 | Le modèle utilisé doit être explicite : equity US américaine ≠ futures option européenne simple. | Natenberg / OCC. | Stocker `model_type` et limites ; warning modèle si American/ex-dividend. |
| MATH-010 | Les chiffres OCR/livres servent à comprendre, pas à calibrer le moteur. | Revue visuelle. | Calibrage uniquement avec data live/historique fiable. |

### C. Construction des structures

| ID | Règle propre | Familles concernées | Action outil |
|---|---|---|---|
| STR-001 | Toute stratégie doit être comparée à `no_trade`, action, option nue et spread simple. | McMillan / Mauboussin. | Comparaison obligatoire avant score final. |
| STR-002 | Achat call/put directionnel exige thèse, horizon, catalyseur, invalidation et IV actuelle. | McMillan / Mauboussin. | Bloquer si thèse ou IV/RV manque. |
| STR-003 | Vertical spread exige net debit/credit exécutable, max loss/gain et risque assignment. | McMillan / Natenberg. | Mid-price interdit comme vérité ; utiliser prix réaliste bid/ask. |
| STR-004 | Calendar/time spread exige surface IV par échéance et événement entre expirations. | Natenberg / McMillan. | Statut `term_structure_or_event_incomplete` si absent. |
| STR-005 | Butterfly/condor exige probabilité de zone, pin risk, open interest et coût multi-jambes. | McMillan / Natenberg. | Veto liquidité/slippage si sortie irréaliste. |
| STR-006 | Ratio/backspread ne passe jamais sans stress risque non borné et marge broker. | McMillan / Natenberg. | `human_validation_required` automatique. |
| STR-007 | Straddle/strangle doit préciser long vol ou short vol et traiter earnings/gaps/IV crush. | Passarelli / Natenberg. | Mode événement obligatoire. |
| STR-008 | Gamma scalping reste `paper_only` tant que données intraday, frais et backtest manquent. | Passarelli. | Log de hedge + P&L attribution obligatoires. |
| STR-009 | Protective/collar/fence doit partir d'un besoin réel de couverture, pas d'un signal de trade. | Natenberg ch. 13. | Exiger portefeuille/exposition à couvrir. |
| STR-010 | LEAPS/substitution action exige liquidité longue, dividendes, borrow, delta drift et plan de sortie. | McMillan. | Vérifier surface IV longue et roll/exit plan. |

### D. Allocation, sizing et portefeuille

| ID | Règle propre | Base documentaire | Action outil |
|---|---|---|---|
| ALLOC-001 | Le sizing part de la perte maximale acceptable, pas de la conviction. | Klarman / Natenberg. | Champ `max_loss_budget` obligatoire. |
| ALLOC-002 | Le risque marginal doit être mesuré contre le portefeuille existant. | Grinold-Kahn. | Exiger positions existantes ou marquer `portfolio_unknown`. |
| ALLOC-003 | Les stratégies à risque non borné ont taille maximale spéciale ou sont interdites. | Natenberg / McMillan. | Veto si max loss non bornée et validation absente. |
| ALLOC-004 | Le rendement sur risque doit être net de coûts et de probabilité de réalisation. | McMillan / Mauboussin. | Score = scénario × probabilité × coûts × liquidité. |
| ALLOC-005 | Une stratégie peu chère peut être mauvaise si la probabilité est trop faible ou l'exécution trop large. | McMillan / Klarman. | Comparer premium faible contre distribution prix/temps. |
| ALLOC-006 | Une stratégie bornée peut être rejetée si la sortie est impraticable. | McMillan / Grinold-Kahn. | `liquidity_veto` prioritaire sur edge. |
| ALLOC-007 | Une stratégie avec beaucoup de jambes doit payer son surcoût de complexité. | McMillan / Grinold-Kahn. | Pénalité commissions/slippage/assignment par jambe. |
| ALLOC-008 | Le turnover prévu est un coût de stratégie, pas un détail opérationnel. | Grinold-Kahn / Passarelli. | Inclure hedge frequency et coût de rebalancement. |
| ALLOC-009 | Toute position doit avoir un plan de réduction ou de sortie si les hypothèses changent. | Natenberg / Douglas. | `close_or_roll_rule` obligatoire. |

### E. Thèse fondamentale TTWO / GTA VI

| ID | Règle propre | Source | Action outil |
|---|---|---|---|
| FUND-001 | La thèse GTA VI doit être séparée du choix de structure optionnelle. | Mauboussin / Klarman. | Deux scores distincts : `underlying_thesis` et `option_structure`. |
| FUND-002 | Le prix TTWO doit être lu comme attentes implicites, pas seulement comme “cher/pas cher”. | Mauboussin. | Reverse DCF/scénarios : unités, prix, marges, timing, RCS. |
| FUND-003 | Un catalyseur doit avoir une date ou fenêtre vérifiable. | Mauboussin / process. | `catalyst_date_range` obligatoire. |
| FUND-004 | Les filings actuels sont nécessaires pour dette, cash-flow, SBC, buybacks et guidance. | SEC EDGAR. | Auto-collect 10-K/10-Q/8-K avant valuation overlay. |
| FUND-005 | La structure optionnelle doit correspondre à l'horizon du catalyseur, pas au récit. | McMillan / Mauboussin. | Expiration doit couvrir fenêtre catalyseur + marge. |
| FUND-006 | Une bonne thèse fondamentale ne compense pas une IV trop chère ou une mauvaise liquidité. | Natenberg / Klarman. | Veto possible par IV/liquidité même si thèse bullish. |
| FUND-007 | Le scénario adverse doit être écrit avant le score. | Klarman / Douglas. | Champ `invalidation` + `adverse_case` obligatoire. |

### F. Processus, décision et journal

| ID | Règle propre | Base documentaire | Action outil |
|---|---|---|---|
| PROC-001 | Le moteur ne transforme jamais une candidate en ordre. | Garde-fou projet. | Sortie max : `research_candidate`, pas `order`. |
| PROC-002 | Chaque score doit expliquer pourquoi la stratégie peut être mauvaise. | Douglas / Klarman. | Bloc `failure_modes` obligatoire. |
| PROC-003 | Une dérogation au plan doit être journalisée avant exécution, pas après. | Douglas. | `plan_deviation_log` obligatoire. |
| PROC-004 | Résultat positif ≠ bonne décision ; résultat négatif ≠ mauvaise décision. | Douglas / Annie Duke. | Post-trade séparant décision, exécution, résultat. |
| PROC-005 | Les sources, données live et timestamps doivent être visibles. | Process research. | Provenance obligatoire dans chaque sortie. |
| PROC-006 | Toute stratégie sensible exige validation humaine : short gamma, risk non borné, marge inconnue, contrat ajusté. | Garde-fou projet. | `human_validation_required` automatique. |

## Matrice de score propre

Le futur score ne doit pas être une note magique. Il doit être une décomposition :

```text
score_total =
  thesis_fit
  + structure_fit
  + expected_value_quality
  + liquidity_quality
  + cost_quality
  + risk_defined_quality
  + execution_quality
  + process_quality
  - veto_penalties
```

Veto avant score :

- contrat non standard non compris ;
- données stale ;
- bid/ask absent ;
- marge inconnue pour short options ou spread complexe ;
- événement earnings/dividende non traité ;
- risque non borné sans validation ;
- no-thesis / no-invalidation ;
- frais ou slippage non estimés.

## Contrat minimal pour TTWO / GTA VI

Avant tout scoring réel, le moteur doit récupérer ou recevoir :

```yaml
underlying:
  ticker: TTWO
  conId:
  exchange:
  currency:
  live_price:
  price_timestamp:
  historical_prices:
  borrow_status:
  dividends:
  corporate_actions:
  next_earnings:
  gta_vi_catalyst_window:

fundamental:
  latest_10k:
  latest_10q:
  latest_8k:
  revenue_scenarios:
  margin_scenarios:
  net_bookings_scenarios:
  debt_cash_sbc_buybacks:
  reverse_dcf_assumptions:
  adverse_case:
  invalidation:

option_chain:
  expirations:
  strikes:
  bid_ask:
  bid_ask_size:
  volume:
  open_interest:
  iv:
  greeks:
  multiplier:
  deliverable:
  exercise_style:
  settlement_cycle:
  adjusted_contract:
  data_timestamp:

execution:
  commissions:
  exchange_fees:
  slippage_model:
  margin_estimate:
  account_permissions:
  multi_leg_executable_price:

decision:
  max_loss_budget:
  comparison_set:
    - no_trade
    - stock
    - long_option
    - vertical_spread
    - alternative_defined_risk
  human_validation:
```

## Ce qu'on peut construire maintenant

1. Un parseur de chaîne options IBKR en lecture seule.
2. Une fiche contrat fiable : multiplier, deliverable, exercise style, bid/ask, IV, Greeks.
3. Un générateur de structures candidates.
4. Un moteur payoff/Greeks/coûts.
5. Un comparateur action vs option vs spread vs no-trade.
6. Un validateur de données et de veto.
7. Un journal de décision.
8. Une couche fondamentale Mauboussin : attentes implicites et scénarios.

## Ce qui reste interdit tant que non validé

- ordre réel ;
- recommandation de trade ;
- short gamma réel ;
- ratio/backspread réel ;
- gamma scalping live ;
- taille de position réelle ;
- utilisation d'une règle issue d'un bloc `to_review` sans promotion.

## Sources actuelles à consulter automatiquement

| Besoin | Source recommandée |
|---|---|
| Settlement / règles US | SEC, OCC ODD |
| Product specs / contract terms | OCC + IBKR contract details |
| Assignment / exercise | OCC ODD + broker |
| Option chain / Greeks / multiplier | IBKR API |
| Commissions / marge | IBKR pricing + margin preview |
| Filings fondamentaux | SEC EDGAR submissions/company facts |
| Taux | U.S. Treasury daily rates ou broker curve |
| Catalyseur GTA VI | Take-Two IR / Rockstar official |

## Décision de travail

Le corpus propre pour la suite est :

1. ce fichier ;
2. `RULES_2026_REVIEW_INDEX.md` pour les 10 règles atomiques déjà normalisées ;
3. `CURRENTNESS_AUDIT_2026.md` pour les règles à actualiser ;
4. `STRATEGY_READINESS_MATRIX.md` pour les familles de stratégies ;
5. `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md` pour l'application au cas TTWO ;
6. les `visual_reviews/` comme preuves documentaires.

Les 365 blocs bruts restent disponibles comme source froide, mais ne doivent pas alimenter le moteur
avant nettoyage.
