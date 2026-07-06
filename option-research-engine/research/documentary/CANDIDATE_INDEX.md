# Index des règles candidates

Date : 2026-07-05

Statut global : `to_review`

Règles normalisées après revue manuelle : 10 sur 216. Elles restent non validées quantitativement et
non actives.

## Interprétation

`Citation vérifiée` signifie uniquement que chaque preuve courte générée existe dans la page PDF
revendiquée. Les règles restent des candidates non actives.

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

- `visual_reviews/B-NATENBERG-1994.md` — figures et tableaux de Natenberg contrôlés page par page.
- `visual_reviews/B-NATENBERG-1994-CH08.md` — structures et sensibilités des volatility spreads.
- `visual_reviews/B-NATENBERG-1994-CH09.md` — comparaison edge théorique, sizing et risques des
  spreads.
