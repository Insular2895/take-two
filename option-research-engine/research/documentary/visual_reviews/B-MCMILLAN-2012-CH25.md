# Revue documentaire — B-MCMILLAN-2012 — Chapitre 25

Source : Lawrence G. McMillan, *Options as a Strategic Investment*, 5e édition.

Chapitre : 25 — LEAPS.

Statut : `to_review`

Date de revue : 2026-07-06.

Périmètre local : pages imprimées `367–389`, pages PDF approximatives `403–429`.

Le texte a été extrait localement avec Transcript. Le segment PDF `419–422`, initialement marqué
`needs_review`, a été rendu en images et contrôlé visuellement. Les exemples datent de l'édition
source : symboles, échéances, fiscalité, règles de marché et standards contractuels ne doivent pas
être transposés directement à IBKR.

## Propriétés générales — pages imprimées 367–373

Les LEAPS sont traitées comme des options actions à longue échéance. Les variables de valorisation
restent les mêmes que pour une option courte, mais leur horizon amplifie :

- le risque de taux ;
- la sensibilité à la volatilité ;
- l'effet des dividendes ;
- le coût d'une erreur d'hypothèse.

La courbe de prix d'une LEAPS est plus plate que celle d'une option courte. La perte de valeur temps
n'est pas linéaire : elle accélère à l'approche de l'échéance.

Les exemples de McMillan indiquent qu'une variation de taux peut modifier de plusieurs points une
LEAPS ITM. Une hausse des dividendes attendus réduit la valeur d'un call et augmente celle d'un put.

## Sensibilités comparées — tableau 25-1, page imprimée 374

Le tableau compare un call à trois mois et un call à deux ans :

| Changement | 20 % OTM, 3 mois / 2 ans | ATM, 3 mois / 2 ans | 20 % ITM, 3 mois / 2 ans |
|---|---:|---:|---:|
| Sous-jacent `+1` | `.03 / .41` | `.54 / .70` | `.97 / .89` |
| Volatilité `+1 point` | `.03 / .43` | `.21 / .48` | `.04 / .33` |
| Taux `+0,5 point` | `.01 / .27` | `.08 / .55` | `.14 / .72` |
| Dividende `+0,25` par trimestre | `0 / -.62` | `-.08 / -1.18` | `-.14 / -1.50` |

Le tableau confirme que la longue échéance accroît fortement l'exposition aux hypothèses de
volatilité, de taux et de dividende. La formule générale « acheter lorsque taux et volatilité sont
bas, vendre lorsqu'ils sont hauts » reste une intuition documentaire, pas une règle exécutable.

## Substitution à l'action et protection — pages imprimées 375–381

Un call LEAPS ITM peut remplacer une partie de l'exposition longue à l'action :

- capital initial inférieur ;
- perte maximale bornée par la prime ;
- capital libéré potentiellement rémunéré ;
- absence de dividende et présence d'une valeur temps à payer.

La comparaison économique doit donc inclure :

- valeur temps de la LEAPS ;
- dividendes abandonnés ;
- intérêt gagné sur le capital libéré ;
- coût de financement évité ;
- fiscalité, commissions, spread et liquidité.

Pour protéger une action, le chapitre compare :

- action longue + put LEAPS ;
- remplacement de l'action par un call LEAPS.

Un put LEAPS ITM peut aussi remplacer une vente à découvert, avec risque borné et sans dividendes à
verser. Cette comparaison dépend toutefois du traitement réel du collatéral, du prêt de titres et
des intérêts chez le courtier.

## Décroissance temporelle — tableau 25-2, page imprimée 384

Tableau contrôlé visuellement :

| Temps restant | Décroissance quotidienne ATM | Décroissance quotidienne 20 % OTM |
|---|---:|---:|
| 24 mois | `.12 %` | `.18 %` |
| 18 mois | `.14 %` | `.27 %` |
| 12 mois | `.19 %` | `.55 %` |
| 9 mois | `.22 %` | `.76 %` |
| 6 mois | `.27 %` | `1.18 %` |
| 3 mois | `.60 %` | `3.57 %` |
| 2 mois | `.73 %` | `4.43 %` |
| 1 mois | `1.27 %` | non renseigné |
| 2 semaines | `3.33 %` | non renseigné |

Même une faible érosion quotidienne composée devient importante. Le texte illustre qu'une perte
d'environ `0,15 %` par jour peut représenter près de `25 %` sur six mois.

## Rollover — pages imprimées 385–386

Heuristiques historiques proposées :

- LEAPS ATM : envisager un roulement lorsqu'il reste environ six mois ;
- LEAPS 20 % OTM : envisager un roulement lorsqu'il reste environ un an ;
- remplacer alors par une LEAPS d'environ deux ans.

Ces seuils proviennent d'exemples anciens. Ils doivent être recalculés à partir du theta, de la
liquidité, du spread, des coûts, de la fiscalité et des échéances réellement disponibles. Ils ne
doivent pas être codés comme déclencheurs automatiques.

## Delta et choix du strike — pages imprimées 386–389

Les LEAPS ont une courbe de delta plus plate :

- une LEAPS ATM à deux ans peut avoir un delta proche de `.70` ;
- les calls ATM et OTM longs peuvent gagner davantage en valeur absolue que leurs équivalents
  courts pour un petit mouvement du sous-jacent ;
- un call très ITM court peut toutefois conserver le delta le plus élevé.

Le chapitre illustre également qu'un strike plus OTM peut produire un rendement en pourcentage
supérieur malgré un gain absolu inférieur. Le choix ne doit donc pas reposer sur le seul levier :
probabilité, horizon, theta, volatilité et perte maximale doivent être comparés.

## Impact projet

Le futur moteur doit :

- annualiser et comparer delta, gamma, theta, vega, rho et exposition dividende par échéance ;
- afficher l'érosion composée et non uniquement le theta instantané ;
- comparer LEAPS, action financée, protective put et vente à découvert après coûts réels ;
- simuler les erreurs de volatilité, taux et dividende sur tout l'horizon ;
- proposer un rollover par optimisation de scénario, jamais par seuil historique codé en dur ;
- signaler les risques de liquidité, spread, exercice anticipé et changement de spécification ;
- conserver toutes les conclusions de ce chapitre en `to_review` jusqu'à validation quantitative.
