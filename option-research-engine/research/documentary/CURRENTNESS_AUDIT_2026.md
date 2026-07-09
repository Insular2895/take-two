# Audit 2026 — ce qui reste actuel et ce qui ne doit pas être repris tel quel

Date : 2026-07-08
Statut : `draft_to_validate`
Périmètre : règles candidates issues de McMillan, Natenberg, Passarelli, Mauboussin, Grinold/Kahn,
Klarman, Lynch et Douglas.

Index règle par règle : `RULES_2026_REVIEW_INDEX.md`.

## Réponse courte

On a suffisamment de matière pour concevoir un **scanner / moteur de recherche en lecture seule**.

On n'a pas encore assez pour exécuter ou recommander des trades réels. Les livres donnent la logique,
les structures, les risques et les formules de base ; les données 2026 doivent venir de sources live
et officielles.

## Stable et réutilisable

| Domaine | Statut 2026 | Commentaire |
|---|---|---|
| Payoffs options | `stable` | Calls, puts, spreads, straddles, strangles, butterflies, collars/fences restent algébriquement valides. |
| Greeks | `stable_but_local` | Delta, gamma, theta, vega sont toujours utiles, mais locaux et dépendants du modèle. |
| Agrégation des risques | `stable` | Calculer les Greeks nets par jambe, stratégie, échéance et portefeuille reste indispensable. |
| IV vs RV | `stable_concept` | L'écart implied/realized reste central, mais ne vaut pas signal seul. |
| Gamma scalping | `stable_concept` | Long gamma : gains de rebalancement doivent couvrir theta et coûts ; short gamma : theta contre risque de gap. |
| Reverse DCF | `stable_concept` | Partir du prix pour remonter aux attentes implicites reste robuste. |
| Scénarios / EV | `stable_concept` | L'espérance pondérée est utile, mais les probabilités doivent être justifiées. |
| Coûts et contraintes | `stable` | Commissions, slippage, bid-ask, marge, borrow et liquidité peuvent retourner un edge brut. |

## À mettre à jour avant usage opérationnel

Ces points ne doivent jamais être repris depuis les livres. Ils doivent être résolus par source
officielle, broker, donnée marché live ou calcul contrôlé.

| Sujet | Pourquoi c'est à jour nécessaire | Source actuelle recommandée | Contrôle à coder avant scoring |
|---|---|---|---|
| Settlement US | Les livres plus anciens citent des environnements pré-T+1. | SEC / OCC : T+1 depuis le 2024-05-28. | Stocker `settlement_cycle` par marché/produit ; refuser tout calcul de cash-flow si le cycle n'est pas connu. |
| Exercise / assignment | Ne jamais coder une hypothèse vague d'exercice automatique. | OCC ODD actuel + règles du broker. | Stocker `exercise_style`, `expiration_type`, seuils/risques d'exercice, risque ex-dividend ; afficher un warning avant toute stratégie short option. |
| Multiplicateur / deliverable | 100 actions est fréquent pour une option equity standard, mais ce n'est pas universel après split, reverse split, spin-off, fusion, dividende spécial ou autre corporate action. | OCC contract specs + IBKR `contractDetails` / `securityDefinitionOptionParameter.multiplier`. | Interdire le hard-code `contracts × 100` ; utiliser `multiplier`, `tradingClass`, `localSymbol`, `conId`, `deliverable`, et marquer `adjusted_contract = true` si contrat non standard. |
| Short sale / uptick | L'ancienne uptick rule décrite dans certains livres n'est pas la règle actuelle. | SEC Regulation SHO Rule 201 + règles broker. | Pour toute couverture par short stock, vérifier `shortable`, borrow/fee, SSR/Rule 201, disponibilité du locate et coût de financement. |
| Stock-options comptables | Les discussions anciennes de Mauboussin ne suffisent plus pour analyser dilution/compensation. | SEC SAB Topic 14 / SAB 120 / ASC 718 + filings. | Ne pas convertir ce sujet en signal trading sans retraitement fondamental : SBC, dilution, rachats compensatoires, notes 10-K/10-Q. |
| Buybacks | Taxe, disclosures et financement modernes peuvent changer l'analyse économique d'un rachat. | IRS Section 4501 + SEC filings. | Ajouter un champ `capital_return_context` : buyback brut, SBC offset, dette utilisée, valorisation, taxe éventuelle, autorisation restante. |
| Taux risk-free | Les exemples de livres sont périmés et les taux changent quotidiennement. | U.S. Treasury daily rates / yield curve, ou courbe broker par devise. | Mapper chaque expiration à un taux par maturité/devise ; ne pas utiliser un taux fixe global. |
| Dividendes / corporate actions | Critique pour options américaines, assignment, forwards, early exercise et modèles. | SEC filings, OCC adjustments, données broker. | Stocker dividendes attendus/ex-date/pay-date, special dividends, splits et ajustements OCC ; stress-test early assignment pour calls short. |
| IV/RV et vol surface | Doit être live, par produit, par expiration et par strike ; une IV moyenne ne suffit pas. | IBKR market data + historique fiable. | Construire surface IV par strike/expiry, RV multi-horizons, IV rank/percentile, skew, term structure ; bloquer si données stale. |
| Marge et commissions | Dépend du compte, du broker, du produit, du pays, du pricing plan et du régime de marge. | IBKR commissions, margin requirements, preview/pre-trade margin. | Estimer coûts par jambe + exchange fees + slippage ; appeler une vérification marge pré-trade en paper/read-only ; refuser short risk si marge inconnue. |

### Implication directe pour le futur outil

Le futur moteur ne doit pas seulement calculer un payoff théorique. Il doit d'abord construire une
fiche contrat fiable :

```text
underlying_conId
option_conId
localSymbol / tradingClass
multiplier
deliverable
exercise_style
expiration
settlement_cycle
corporate_action_adjusted
bid / ask / size / volume / open_interest
iv / greeks / model_source
margin_estimate
commission_estimate
data_timestamp
```

Si une de ces données manque, le statut de la stratégie doit rester `data_incomplete`, pas
`candidate_trade`.

## Sources externes vérifiées

- SEC — T+1 standard settlement cycle, compliance date 2024-05-28 : https://www.sec.gov/exams/educationhelpguidesfaqs/t1-faq
- SEC — communiqué T+1 du 2024-05-21 : https://www.sec.gov/newsroom/press-releases/2024-62
- OCC — ODD *Characteristics and Risks of Standardized Options*, version juin 2024 : https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document
- OCC — ODD update T+1 / MEMX, juin 2024 : https://www.theocc.com/getmedia/31a1f0fc-f7e7-477c-9c03-f84d1dd05cf6/june_2024_supplement.pdf
- OCC — equity options product specifications / 100 shares standard and adjusted contracts : https://www.theocc.com/clearance-and-settlement/clearing/equity-options-product-specifications
- SEC — SAB Topic 14, share-based payment / expected volatility : https://www.sec.gov/interps/account/sabcodet14.htm
- SEC — SAB 120, ASC 718 and share-based payment : https://www.sec.gov/rules-regulations/staff-guidance/staff-accounting-bulletins/staff-accounting-bulletin-120
- SEC — alternative uptick rule / Rule 201 : https://www.sec.gov/news/press/2010/2010-26.htm
- IRS — stock repurchase excise tax, Section 4501 : https://www.irs.gov/irb/2025-51_IRB
- U.S. Treasury — daily rates / interest-rate statistics : https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics
- SEC — EDGAR APIs / company facts and submissions : https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- IBKR TWS API — option chains via `reqSecDefOptParams` : https://interactivebrokers.github.io/tws-api/options.html
- IBKR TWS API — `securityDefinitionOptionParameter` returns `multiplier`, expirations and strikes : https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html
- IBKR — options commissions : https://www.interactivebrokers.com/en/pricing/commissions-options.php
- IBKR — margin rates and financing : https://www.interactivebrokers.com/en/trading/margin-rates.php
- IBKR Campus — margin requirements / real-time margining : https://www.interactivebrokers.com/campus/glossary-terms/margin-requirements/

## Verdict

Les livres sont encore très utiles comme **architecture de raisonnement**, mais pas comme source de
paramètres 2026.

Règle de travail pour la suite :

```text
Livre = logique / structure / risques / formule de base.
Donnée 2026 = source officielle, broker, marché live, filing ou backtest.
Trade réel = interdit sans validation humaine explicite.
```
