# Index des règles candidates

Date : 2026-07-05

Statut global : `to_review`

Règles normalisées après revue manuelle : 10 sur 216. Elles restent non validées quantitativement et
non actives.

Revue de validité 2026 des 10 règles normalisées :
`RULES_2026_REVIEW_INDEX.md`.

Plan de traitement du backlog 216 / 365 :
`ATOMIC_RULE_BACKLOG_PLAN.md`.

Corpus propre utilisable pour concevoir le futur moteur read-only :
`CLEAN_USABLE_RULESET_2026.md`.

## Interprétation

`Citation vérifiée` signifie uniquement que chaque preuve courte générée existe dans la page PDF
revendiquée. Les règles restent des candidates non actives.

Important : les `216` entrées ne sont pas 216 fichiers de règles prêts à coder. Ce sont des candidats
documentaires. Les `365` blocs restent un backlog `to_review`.

| Source | Règles avec citation vérifiée | Règles issues de blocs à revoir |
|---|---:|---:|
| McMillan | 22 | 33 |
| Natenberg | 59 | 18 |
| Passarelli | 20 | 14 |
| Douglas | 16 | 51 |
| Grinold et Kahn | 28 | 30 |
| Klarman | 8 | 29 |
| Mauboussin et Rappaport | 43 | 106 |
| Lynch | 20 | 77 |
| Notes secondaires sur Annie Duke | 0 | 7 |
| **Total** | **216** | **365** |

## Priorités de revue

### Priorité A — futur contrat de risque

- agrégation des Greeks ;
- theoretical edge et sensibilité aux hypothèses ;
- gamma/theta et coût du rebalancement ;
- risque de gap, skew et structure par terme ;
- liquidité, bid-ask et exécution multi-jambes ;
- contraintes, turnover et coûts.

### Priorité B — sélection du sous-jacent

- attentes implicites et reverse DCF ;
- marge de sécurité et valorisation indépendante ;
- dette, dilution, cash-flow et détérioration de la thèse ;
- analyse contradictoire et conditions de sortie.

### Priorité C — garde-fous du processus

- conformité entre plan et exécution ;
- acceptation préalable du risque ;
- journal post-trade ;
- distinction entre qualité de décision et résultat.

## Règles de promotion

Une candidate ne peut devenir `documentary_validated` qu'après vérification manuelle de :

1. la page et le contexte complet ;
2. la fidélité de la condition ;
3. la fidélité de l'action ;
4. l'absence de seuil inventé ;
5. les exceptions et limites ;
6. la compatibilité avec l'édition citée.

Même après cette promotion, elle reste inactive jusqu'à validation quantitative et décision
explicite.

## Première passe normalisée

- `R-GREEKS-001` — agrégation des Greeks ;
- `R-GREEKS-002` — neutralité delta instantanée et recalcul ;
- `R-GREEKS-003` — économie gamma/theta nette des coûts ;
- `R-GREEKS-004` — normalisation des signes et unités des Greeks ;
- `R-VOL-001` — marge d'erreur sur la volatilité ;
- `R-OPTIONS-001` — edge net et exécutabilité multi-jambes.
- `R-RISK-001` — edge après contraintes et coûts ;
- `R-VALUATION-001` — attentes implicites du sous-jacent ;
- `R-DECISION-001` — thèse falsifiable et analyse contradictoire ;
- `R-PSY-001` — traçabilité des dérogations au plan.

## Revues visuelles en cours

- `visual_reviews/B-MCMILLAN-2012-CH03.md` — achat de calls, choix du strike et de l'échéance,
  delta, horizon et critères de sélection.
- `visual_reviews/B-MCMILLAN-2012-CH07.md` — bull spreads, agressivité, comparaison au call sec et
  actions de suivi.
- `visual_reviews/B-MCMILLAN-2012-CH09.md` — fin du chapitre sur les calendar spreads, revue
  partielle.
- `visual_reviews/B-MCMILLAN-2012-CH10.md` — butterfly spreads, sélection, coûts et suivi.
- `visual_reviews/B-MCMILLAN-2012-CH11.md` — début des ratio call spreads et risque haussier non
  borné, revue partielle.
- `visual_reviews/B-MCMILLAN-2012-CH25.md` — LEAPS, sensibilités longues, substitution à l'action,
  décroissance temporelle et rollover.
- `visual_reviews/B-NATENBERG-1994-CH04.md` — fondations volatilité, IV, annualisation et marge
  d'erreur.
- `visual_reviews/B-NATENBERG-1994-CH05.md` — theoretical edge, delta hedge dynamique et coûts
  réels.
- `visual_reviews/B-NATENBERG-1994.md` — figures et tableaux de Natenberg contrôlés page par page.
- `visual_reviews/B-NATENBERG-1994-CH08.md` — structures et sensibilités des volatility spreads.
- `visual_reviews/B-NATENBERG-1994-CH09.md` — comparaison edge théorique, sizing et risques des
  spreads.
- `visual_reviews/B-NATENBERG-1994-CH13.md` — hedging avec options, protective options, covered
  writes, fences/collars et portfolio insurance.
- `visual_reviews/B-PASSARELLI-2012-CH13.md` — gamma scalping, long/short gamma, theta et
  politiques de hedge.
- `visual_reviews/B-PASSARELLI-2012-VOL-CHARTS.md` — configurations IV/RV et lecture des
  divergences/convergences de volatilité.
- `visual_reviews/B-GRINOLD-KAHN-1999-CORE.md` — risque, information ratio, loi fondamentale,
  covariance, contraintes, turnover et coûts.
- `visual_reviews/B-MAUBOUSSIN-RAPPAPORT-2001.md` — attentes implicites, reverse DCF, scénarios,
  M&A, buybacks et couche thèse du sous-jacent.
- `CURRENTNESS_AUDIT_2026.md` — audit des concepts encore actuels et des données/règles à mettre à
  jour avec sources officielles.
- `STRATEGY_READINESS_MATRIX.md` — matrice de construction des familles de stratégies et données
  manquantes avant usage réel.
- `CLEAN_USABLE_RULESET_2026.md` — version nettoyée et utilisable du corpus : règles propres,
  bruit exclu, veto 2026, contrat de données et frontière read-only/paper.
- `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md` — application du corpus au cas TTWO / GTA VI, avec
  données live nécessaires, garde-fous et comparaison action/call/spreads avant build IBKR.
- `READING_GUIDE.md` — chemin de lecture humain pour reprendre la recherche sans relire la
  conversation.
- `SOURCE_GAPS.md` — sources réellement manquantes et règle de demande de nouvelles captures.
