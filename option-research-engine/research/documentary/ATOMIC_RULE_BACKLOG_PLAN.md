# Plan de backlog — 216 candidats et 365 blocs `to_review`

Date : 2026-07-09
Statut : `draft_to_validate`
Objet : expliquer quoi faire des 216 candidats documentaires et des 365 blocs à revoir avant de
construire le moteur d'options TTWO/GTA VI.

## Réponse courte

Les 216 candidats ne doivent pas être transformés automatiquement en 216 règles actives.

Ils deviennent un **backlog de matière première**. On les utilise pour nourrir le futur moteur, mais
seulement après promotion progressive :

```text
candidat documentaire
→ règle atomique à revoir
→ règle documentaire validée
→ règle testable
→ règle utilisable par le moteur en read-only
→ règle active seulement après validation humaine et données live
```

Les 365 blocs restent en `to_review` tant qu'ils ne sont pas nettoyés, dédoublonnés et reliés à une
source précise.

## Pourquoi ne pas tout transformer maintenant ?

Créer 216 fichiers de règles maintenant donnerait une fausse impression de précision.

Une règle utile au moteur doit être :

- atomique : une condition, une action, une limite ;
- sourcée : page ou passage identifié ;
- non redondante avec une règle existante ;
- compatible avec les données 2026 ;
- testable par le futur outil ;
- bloquée si les données live ou broker manquent.

Sans cela, on obtiendrait des pseudo-règles difficiles à maintenir et dangereuses pour un moteur de
scoring d'options.

## Ce qu'on en fait concrètement

### Priorité A — contrat de risque du futur trade

Objectif : construire d'abord le noyau qui empêche le moteur de raconter n'importe quoi.

À extraire en premier :

- agrégation des Greeks ;
- delta net par jambe, stratégie, expiration et portefeuille ;
- gamma/theta net des coûts ;
- vega, skew, term structure et marge d'erreur sur volatilité ;
- bid/ask, slippage, open interest, volume et exécution multi-jambes ;
- marge, assignment, early exercise, ex-dividend, settlement et multiplicateur ;
- stress de gap, IV crush, halt, earnings et événement majeur ;
- statut `no_trade` obligatoire si l'edge ne survit pas aux contraintes.

Sortie attendue :

- règles `R-GREEKS-*`, `R-VOL-*`, `R-OPTIONS-*`, `R-RISK-*` ;
- tests unitaires de calcul ;
- blocage automatique si donnée live absente.

### Priorité B — sélection du sous-jacent

Objectif : relier la thèse TTWO/GTA VI à une structure optionnelle, au lieu de choisir une option
juste parce que l'histoire paraît bullish.

À extraire ensuite :

- attentes implicites et reverse DCF ;
- scénarios de revenus, marge, cash-flow et timing GTA VI ;
- dette, dilution, stock-based compensation, buybacks et capital allocation ;
- marge de sécurité ;
- analyse contradictoire ;
- conditions d'invalidation ;
- comparaison action vs call/put vs vertical vs calendar vs no-trade.

Sortie attendue :

- règles `R-VALUATION-*`, `R-UNDERLYING-*`, `R-SCENARIO-*` ;
- grille de scénario fondamental ;
- lien explicite entre thèse fondamentale et structure option.

### Priorité C — garde-fous de décision

Objectif : empêcher le moteur de transformer un bon récit ou un bon backtest en décision non
contrôlée.

À extraire en dernier :

- conformité entre plan pré-trade et exécution ;
- acceptation préalable du risque ;
- taille maximale ;
- validation humaine obligatoire pour short risk, ratio spread, gamma scalping ou trade réel ;
- journal post-trade ;
- distinction entre bonne décision et bon résultat ;
- règles d'arrêt, roll, close et invalidation.

Sortie attendue :

- règles `R-DECISION-*`, `R-PSY-*`, `R-JOURNAL-*` ;
- template de plan pré-trade ;
- template de post-mortem ;
- politique de dérogation.

## Statuts à utiliser

| Statut | Signification | Utilisable par le moteur ? |
|---|---|---|
| `to_review` | Bloc brut ou formulation non fiable | Non |
| `candidate_documentary` | Passage identifié, mais pas encore atomisé | Non |
| `documentary_validated` | Citation et contexte validés | Non, sauf affichage recherche |
| `testable_rule` | Condition/action/limites transformées en logique testable | Oui en simulation |
| `read_only_gate` | Peut bloquer ou scorer en lecture seule | Oui en research engine |
| `active_after_human_validation` | Peut être utilisé dans un workflow opérationnel validé | Seulement après validation explicite |

## Structure cible du backlog

Chaque future entrée atomisée devrait suivre ce format :

```yaml
id: R-DOMAIN-###
status: to_review
priority: A|B|C
source:
  book:
  page:
  figure_or_table:
rule:
  condition:
  action:
  rationale:
limits:
  -
requires_live_data:
  -
blocks_if_missing:
  -
tool_module:
  - pricing
  - risk
  - execution
  - valuation
  - decision
```

## Application directe au projet TTWO/GTA VI

Pour construire le futur outil, on ne doit pas attendre que les 216 candidats soient tous promus.

On doit d'abord promouvoir assez de règles Priorité A pour produire une fiche stratégie fiable :

```text
structure
legs
payoff
net debit / credit
max loss
max gain
break-even
delta / gamma / theta / vega nets
IV vs RV
bid/ask et liquidité
marge
assignment / ex-dividend
stress scenarios
statut no-trade si edge insuffisant
```

Ensuite seulement on ajoute la Priorité B pour relier le trade à la thèse fondamentale TTWO, puis la
Priorité C pour encadrer le comportement humain et les dérogations.

## Décision de travail

```text
Les 216 candidats servent de carburant.
Les 365 blocs servent de mine à nettoyer.
Les 10 règles atomiques servent de socle.
Le futur moteur ne consomme que des règles testables, sourcées et bloquées par données live.
```
