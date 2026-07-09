# Pondération des sources

## Objectif

Le futur moteur ne doit pas donner le même poids à un livre spécialisé, une documentation officielle,
un repository GitHub et un article de blog. Ce fichier fixe la hiérarchie de confiance utilisée pour
interpréter les sources avant de pondérer les règles dans `docs/04_ponderation_des_regles.md`.

## Hiérarchie de confiance

| Niveau | Source | Usage principal | Peut valider seul ? |
|---:|---|---|---|
| 5 | Source officielle actuelle : SEC, OCC, IRS, Treasury, IBKR, filings SEC, contract specs, corporate actions | Données 2026, réglementation, broker, fiscalité, settlement, marge, deliverables | Oui pour son domaine |
| 4 | Livres spécialistes du domaine : Natenberg, McMillan, Passarelli, Hull, Taleb, Sinclair | Structure optionnelle, Greeks, volatilité, payoff, risques de stratégie | Oui pour principes théoriques, non pour données live |
| 4 | Livres fondamentaux / portefeuille : Mauboussin, Klarman, Lynch, Grinold-Kahn, Vince | Thèse sous-jacente, attentes implicites, marge de sécurité, allocation | Oui pour méthode, non pour données actuelles |
| 3 | Papers académiques, manuels techniques, documentation de modèles reconnus | Méthodes quantitatives, backtesting, robustesse | Oui si le contexte correspond |
| 2 | Repositories open source étudiés : GS Quant, OpTrade, GraphVega, Keeks, etc. | Inspiration d'architecture, benchmark, visualisation, patterns de données | Non |
| 1 | Blogs, forums, newsletters, posts sociaux, exemples isolés | Idées, signaux faibles, questions à tester | Non |

Règle simple : pour les options, **Natenberg / McMillan / Passarelli pèsent plus qu'un blog ou un
repo GitHub**. En revanche, si une règle de livre contredit une source officielle actuelle, la source
officielle gagne dans son domaine.

## Arbitrage des conflits

1. Si le conflit concerne une règle actuelle de marché, broker, fiscalité, exercice, assignment,
   settlement ou corporate action : source officielle actuelle > livre ancien.
2. Si le conflit concerne une logique de stratégie optionnelle : livre spécialiste > repo GitHub >
   blog.
3. Si le conflit concerne l'implémentation logicielle : documentation officielle de l'API ou tests
   locaux > repo tiers > blog.
4. Si deux sources de même niveau divergent : statut `CONTRADICTED` ou `DRAFT` jusqu'à simulation ou
   validation humaine.

## Effet sur les règles

La pondération effective reste calculée dans `docs/04_ponderation_des_regles.md`, mais le facteur
`confiance_source` doit être dérivé de cette hiérarchie et de la catégorie concernée.

Une règle peut avoir une source très forte et rester inutilisable si :

- elle n'a pas de condition testable ;
- elle dépend de données live manquantes ;
- elle est contredite par le broker ou la réglementation actuelle ;
- elle n'a pas de dossier de preuve dans `evidence/`.
