# Architecture - TTWO options budget engine V9

## Objectif

V9 repond a une contrainte de capital de EUR 1 000 sans transformer le moteur read-only en outil
d'execution. Elle compare un vertical call longue echeance unique a un plan en trois poches :
court, moyen et long. Une structure ne peut contribuer aux statistiques ou apparaitre comme
candidate si son risque modelise depasse sa poche.

## Faits sources

- Snapshot options : MarketData.app EOD au 2026-07-16.
- Chaine actuelle : export Alpaca read-only ; derniere echeance disponible 2027-03-19, 246 DTE.
- Change : BCE, 2026-07-17, `1 EUR = 1.1435 USD`.
- Budget : EUR 1 000 defini par l'utilisateur.

Le change sert uniquement a comparer le risque USD modelise au budget EUR. IBKR peut appliquer un
autre taux et d'autres couts au moment d'une simulation ou d'un ordre paper.

## Plans explores

| Plan | Poche | Budget | DTE cible | Sortie de recherche |
| --- | --- | ---: | ---: | --- |
| `single_long` | long | EUR 1 000 | 270 | TP +80 %, stop -50 %, 30 seances |
| `staged_three` | court | EUR 310 | 45 | TP +50 %, stop -40 %, 5 seances |
| `staged_three` | moyen | EUR 245 | 150 | TP +70 %, stop -50 %, 20 seances |
| `staged_three` | long | EUR 445 | 270 | TP +80 %, stop -50 %, 30 seances |

Ces poids sont des hypotheses `draft_to_validate`, pas une allocation adoptee. Les trois poches ne
sont pas trois achats obligatoires : chacune doit passer independamment budget, liquidite,
historique, holdout et verification broker.

## Regles moteur

1. La fixture declare `budget_plan_id`, `budget_bucket`, `budget_eur`, `eur_usd_rate` et sa date.
2. Pour chaque cas historique, le risque USD borne est estime aux prix executables EOD.
3. Si `risk_usd > budget_eur * eur_usd_rate`, le cas est ignore avec une raison auditable.
4. Le scan actuel applique le meme veto avant de determiner `eligible`, `watchlist` ou `blocked`.
5. L'absence de contrat conforme laisse la poche vide ; aucun filtre de liquidite n'est assoupli.

## Resultat du run V9

### Un seul trade long

Le scan construit un bull call spread mars 2027 : achat C250 a l'ask EOD 38.30 et vente C270 au
bid EOD 27.80. Le debit indicatif est USD 10.50 par action, soit USD 1 050 par lot. Avec les couts
modelises, le risque maximal estime est USD 1 058.60, environ EUR 925.75, et le gain terminal
maximal estime est USD 941.40.

Le point mort terminal hors nouveaux frais est proche de USD 260.50 pour TTWO. Ce payoff n'est
valable qu'a l'echeance ; la recette ferme plus tot a TP, stop ou apres 30 seances. Le candidat est
`blocked` : echantillons train/test, couverture et holdout insuffisants. Il ne constitue donc pas
un ordre a reproduire.

### Plan en trois temps

- Court : aucune jambe conforme. Les strikes proches de la cible ont des spreads bid/ask au-dessus
  du seuil de 30 %.
- Moyen : aucune jambe conforme pour la cible tres OTM sous le meme filtre de liquidite.
- Long : C310/C320 mars 2027, risque estime USD 508.60, environ EUR 444.77. La variante est bloquee
  par rendement median, drawdown, pire perte, robustesse, instabilite et holdout.

Le plan trois temps n'est donc pas complet : une seule poche sur trois est actuellement
construisible et sa preuve historique est defavorable.

## Decision de recherche

Le classement reste `no_trade`. Cela signifie : aucune structure ne passe aujourd'hui tous les
controles. Cela ne signifie ni que TTWO va baisser, ni qu'aucun trade futur ne sera possible. Une
nouvelle chaine, une echeance plus lointaine, des spreads plus serres et une periode holdout fraiche
peuvent changer le diagnostic.

## Limites

- EOD bid/ask, pas de combo quote ou replay intraday.
- Maximum cote a 246 DTE, pas un an exact.
- Une annee d'historique fournisseur, avec tres petits echantillons aux longues maturites.
- Pas de fill, marge, permissions, fiscalite ou change IBKR verifies.
- Le taux de gain historique n'est pas une probabilite calibree du prochain trade.
