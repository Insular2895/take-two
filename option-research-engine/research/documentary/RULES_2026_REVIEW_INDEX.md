# Revue 2026 des règles normalisées

Date : 2026-07-08
Statut : `draft_to_validate`
Périmètre : les 10 règles déjà normalisées en fichiers dans `option-research-engine/rules/`.

## Résultat court

Les 10 règles normalisées restent valides comme **cadre de raisonnement** en 2026.

Aucune ne doit être considérée comme active pour un trade réel. Elles restent bloquées tant que le
futur outil n'a pas les données live, les contrôles broker, les coûts, la marge, les règles
d'exécution et la validation humaine.

## Clarification 216 / 365

- `216` = candidats avec citation vérifiée dans les sources documentaires.
- `365` = formulations/blocs à revoir avant normalisation.
- `10` = règles déjà promues en fichiers atomiques.

Cette revue porte sur les 10 règles atomiques, pas sur une promotion automatique des 216 candidats.
Les 216 et 365 restent un backlog `to_review`.

## Carte règle par règle

| # | Règle | Fichier | Validité 2026 | Ce qui bloque l'usage réel |
|---:|---|---|---|---|
| 1 | `R-GREEKS-001` — Agréger les Greeks | [rules/GREEKS/R-GREEKS-001.md](../../rules/GREEKS/R-GREEKS-001.md) | `valide_comme_principe` | Multiplicateur, deliverable, convention, modèle et timestamp doivent venir de données contrat live. |
| 2 | `R-GREEKS-002` — Recalculer la neutralité delta | [rules/GREEKS/R-GREEKS-002.md](../../rules/GREEKS/R-GREEKS-002.md) | `valide_comme_principe` | Politique de hedge, exercise/assignment, ex-dividend, settlement, coûts et validation humaine. |
| 3 | `R-GREEKS-003` — Gamma/theta net des coûts | [rules/GREEKS/R-GREEKS-003.md](../../rules/GREEKS/R-GREEKS-003.md) | `valide_comme_principe` | Backtest, paper trading, logs de hedge, frais, slippage, gaps, latence et événements. |
| 4 | `R-GREEKS-004` — Normaliser signes et unités | [rules/GREEKS/R-GREEKS-004.md](../../rules/GREEKS/R-GREEKS-004.md) | `valide_comme_principe` | Convention fournisseur, unités, devise, multiplicateur, modèle et signe de position. |
| 5 | `R-VOL-001` — Marge d'erreur sur volatilité | [rules/VOL/R-VOL-001.md](../../rules/VOL/R-VOL-001.md) | `valide_comme_principe` | Surface IV live, skew, term structure, RV multi-horizons, événements et stress scenarios. |
| 6 | `R-OPTIONS-001` — Edge net exécutable | [rules/OPTIONS/R-OPTIONS-001.md](../../rules/OPTIONS/R-OPTIONS-001.md) | `valide_comme_principe` | Bid/ask réel, net debit/credit, commissions, slippage, open interest, marge et preview exécution. |
| 7 | `R-RISK-001` — Edge après contraintes | [rules/RISK/R-RISK-001.md](../../rules/RISK/R-RISK-001.md) | `valide_comme_principe` | Marge, permissions, borrow, Rule 201, stress gaps/halts/IV crush, taille max et validation humaine. |
| 8 | `R-VALUATION-001` — Attentes implicites | [rules/VALUATION/R-VALUATION-001.md](../../rules/VALUATION/R-VALUATION-001.md) | `valide_comme_principe` | Filings actuels, WACC, comparables, dette, dilution, buybacks, fiscalité et scénarios validés. |
| 9 | `R-DECISION-001` — Thèse falsifiable | [rules/DECISION/R-DECISION-001.md](../../rules/DECISION/R-DECISION-001.md) | `valide_comme_principe` | Thèse TTWO/GTA VI, catalyseur, invalidation, comparaison action/option/spread/no-trade. |
| 10 | `R-PSY-001` — Traçabilité des dérogations | [rules/PSY/R-PSY-001.md](../../rules/PSY/R-PSY-001.md) | `valide_comme_principe` | Plan pré-trade, risque accepté, journal, post-mortem, logs broker/paper et escalade humaine. |

## Sources 2026 à utiliser par le futur outil

| Domaine | Source actuelle recommandée | Usage dans le moteur |
|---|---|---|
| Settlement US | SEC T+1 | Cycle de cash-flow et dates de règlement. |
| ODD, exercise, assignment | OCC ODD actuel | Risques standardisés, exercice, assignment et options américaines. |
| Multiplicateur / contrats ajustés | OCC contract specs + IBKR contract details | Interdire le hard-code `contrats × 100`. |
| Short sale / SSR | SEC Regulation SHO Rule 201 + broker | Couverture short stock, locate, borrow, SSR. |
| Taux risk-free | U.S. Treasury daily rates / courbe broker | Mapping par maturité/devise. |
| Filings fondamentaux | SEC EDGAR APIs / filings société | Reverse DCF, dette, dilution, buybacks, SBC. |
| Stock compensation | SEC SAB Topic 14 / SAB 120 / ASC 718 | Retraitement SBC/dilution. |
| Buybacks | IRS Section 4501 + filings SEC | Contexte fiscal et économique des rachats. |
| Options chain, Greeks, IV, marge | IBKR market data, contract details, margin/commission endpoints | Données live, coût, marge, exécution et statut broker. |

## Décision de validité

```text
Livre = logique / structure / risques / formule de base.
Donnée 2026 = source officielle, broker, marché live, filing ou backtest.
Règle = non active tant qu'elle n'a pas ses données 2026 et une validation humaine.
Trade réel = interdit sans validation explicite.
```

## Prochaine étape recommandée

Transformer les 216 candidats en backlog atomique, mais seulement par ordre de priorité :

1. risque/Greeks/exécution ;
2. thèse fondamentale et attentes implicites ;
3. garde-fous de décision et journal.

Cela évite de créer 216 pseudo-règles non fiables alors que seules les règles déjà normalisées sont
utilisables pour concevoir le futur outil.
