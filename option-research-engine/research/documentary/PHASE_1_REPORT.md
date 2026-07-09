# Phase 1 — Recherche documentaire

Date : 2026-07-05

Statut : `research_complete_rules_to_review`

## Réponse de la phase

Le corpus permet de définir l'architecture intellectuelle du futur outil IBKR, mais pas encore
d'activer des règles de trading.

Le moteur devra séparer cinq couches :

1. qualité et valorisation du sous-jacent ;
2. scénario et horizon ;
3. prix de la volatilité et choix de structure ;
4. risque agrégé de position ;
5. exécution, coûts et discipline.

La recherche a produit 216 règles candidates dont la preuve courte est retrouvée sur la page PDF
revendiquée. Ce contrôle est documentaire et déterministe. Il ne prouve ni que l'interprétation de
Gemini est fidèle, ni que la règle est rentable, ni qu'elle est adaptée au marché actuel.

La revue manuelle a trouvé plusieurs transformations abusives d'une observation en prescription.
Une seconde passe ciblée a normalisé dix règles dont le contexte complet soutient la condition et
l'action. Elles ne sont ni `VALIDÉES` quantitativement ni `ACTIVES`.

## Corpus et couverture

| Source | Blocs | Citation vérifiée | À revoir | Sans règle | Échec final |
|---|---:|---:|---:|---:|---:|
| McMillan, 5e éd. | 32 | 13 | 13 | 6 | 0 |
| Natenberg | 53 | 36 | 8 | 9 | 0 |
| Passarelli | 31 | 18 | 9 | 4 | 0 |
| Douglas | 44 | 12 | 29 | 3 | 0 |
| Grinold et Kahn, 2e éd. | 50 | 23 | 20 | 7 | 0 |
| Klarman | 13 | 3 | 10 | 0 | 0 |
| Mauboussin et Rappaport, éd. 2001 | 60 | 18 | 41 | 1 | 0 |
| Lynch, Millennium Edition | 34 | 8 | 26 | 0 | 0 |
| Notes secondaires sur Annie Duke | 2 | 0 | 2 | 0 | 0 |
| **Total** | **319** | **131** | **158** | **30** | **0** |

Les 131 blocs avec citation vérifiée contiennent 216 règles candidates. Un bloc peut contenir
plusieurs règles.

## Apports robustes pour le futur outil

### 1. Mesurer la position entière, pas une option isolée

Natenberg indique que delta, gamma, theta et vega sont additifs au niveau d'une position
(`B-NATENBERG-1994`, chapitre 6, PDF p. 134). Le futur moteur devra donc calculer les Greeks nets
par sous-jacent, échéance et portefeuille, avant tout classement d'un contrat.

Conséquence de conception : aucun score d'option ne doit être présenté sans son impact marginal sur
les expositions déjà détenues.

### 2. Un edge théorique dépend des hypothèses

Natenberg définit l'edge à partir de l'écart entre valeur théorique et prix de transaction
(`B-NATENBERG-1994`, chapitre 6, PDF p. 134), mais insiste aussi sur l'incertitude de l'estimation de
volatilité : une marge d'un point peut être insuffisante (`B-NATENBERG-1994`, chapitre 4, PDF
p. 91).

Conséquence de conception : stocker le modèle, ses entrées, la sensibilité aux erreurs d'IV et un
intervalle de robustesse. Un simple `fair_value - mid_price > 0` ne suffit pas.

### 3. Gamma, theta et volatilité réalisée forment un seul problème

Passarelli formule l'objectif d'un long gamma delta-neutre : les gains de rebalancement doivent
couvrir le theta (`B-PASSARELLI-2012`, chapitre 13, PDF p. 272-273). Natenberg décrit le
rééquilibrage comme une succession de petits paris (`B-NATENBERG-1994`, chapitre 5, PDF p. 94).

Conséquence de conception : toute stratégie de gamma scalping devra être évaluée nette des spreads,
commissions, slippage, fréquence de hedge et gaps. La comparaison IV/RV seule ne constitue pas une
règle d'entrée.

### 4. La structure doit être comparée à une alternative plus simple

McMillan compare achat de call, bull spread et LEAPS selon l'horizon et le risque. Natenberg rappelle
qu'un spread à trois côtés peut être plus difficile et plus coûteux à exécuter qu'une structure à
deux côtés (`B-NATENBERG-1994`, chapitre 9, PDF p. 191).

Conséquence de conception : le moteur devra comparer au minimum l'option nue, le spread vertical,
l'action et l'absence de trade, sur une base de P&L net et de liquidité.

### 5. Le sous-jacent a besoin d'une thèse falsifiable

Mauboussin et Rappaport proposent de partir du prix pour retrouver les attentes implicites de flux
(`B-MAUBOUSSIN-RAPPAPORT-2001`, chapitre 1, PDF p. 27), puis de chercher activement ce qui contredit
la thèse (`B-MAUBOUSSIN-RAPPAPORT-2001`, chapitre 5, PDF p. 119). Lynch demande une explication
courte de la thèse avant achat (`B-LYNCH-2000`, chapitre 11, PDF p. 165). Klarman exige une
valorisation indépendante (`B-KLARMAN-1991`, chapitre 10, PDF p. 173).

Conséquence de conception : une option ne doit pas être sélectionnée uniquement à partir de sa
chaîne. Le dossier doit contenir scénario, catalyseur, attentes implicites et condition
d'invalidation.

### 6. La qualité brute d'un signal doit survivre aux contraintes

Grinold et Kahn relient skill, nombre de paris indépendants et information ratio
(`B-GRINOLD-KAHN-1999`, chapitre 6, PDF p. 168). Leur partie implémentation traite explicitement
turnover, contraintes et coûts (`B-GRINOLD-KAHN-1999`, chapitres 14-16).

Conséquence de conception : séparer score brut, corrélation entre signaux, capacité, coûts
d'exécution et performance nette. Le nombre d'opportunités ne doit jamais être assimilé sans test au
nombre de paris indépendants.

### 7. Le processus doit empêcher l'improvisation

Douglas traite l'acceptation préalable du risque (`B-DOUGLAS-2000`, PDF p. 40) et l'écart entre
trade planifié et trade exécuté (PDF p. 14 et 34). Ces passages soutiennent des garde-fous de
processus, pas des signaux de marché.

Conséquence de conception : journaliser scénario initial, risque accepté, motif d'entrée, motif de
sortie et toute dérogation. Une règle comportementale ne doit pas bloquer automatiquement un ordre
sans définition opérationnelle validée.

## Données minimales à prévoir pour la phase IBKR

Cette liste est une exigence de recherche, pas une décision d'implémentation :

- chaîne complète : bid, ask, tailles, volume, open interest, strike, échéance ;
- sous-jacent, dividendes, taux, calendrier d'événements et corporate actions ;
- IV par strike et maturité, surface/skew, historique d'IV et volatilité réalisée ;
- delta, gamma, theta, vega, rho par jambe et agrégés ;
- modèle de valorisation, hypothèses et sensibilités ;
- commissions, slippage estimé, multiplicateur et marge ;
- scénario de prix/temps/IV, horizon, objectif et invalidation ;
- positions et ordres existants pour mesurer le risque marginal ;
- journal de décision et résultat net.

## Limites

- Le corpus est majoritairement ancien ; règles de marché, seuils d'exercice et microstructure
  doivent être revérifiés avec des sources actuelles avant implémentation.
- Les PDF Natenberg et Passarelli sont issus d'OCR. Les tableaux et formules prioritaires des
  chapitres documentés ont été revus visuellement ; toute section non encore revue reste impropre à
  un usage quantitatif automatique.
- L'édition Mauboussin traitée est celle de 2001, pas la révision 2021.
- Le fichier Annie Duke est un résumé tiers de 15 pages. Il ne valide aucune citation du livre.
- Une preuve courte retrouvée ne valide pas les champs `Action`, `Condition` ou `Exceptions` générés
  par Gemini.
- Aucun backtest, aucune donnée IBKR et aucune validation de rentabilité n'ont été réalisés.

## Décision de passage

La phase documentaire est suffisamment avancée pour concevoir ensuite le contrat de données et le
mode lecture seule d'IBKR.

Un audit de fraîcheur 2026 a été ajouté dans `CURRENTNESS_AUDIT_2026.md`. Il confirme que les livres
restent utiles pour la logique, les structures et les risques, mais que les paramètres opérationnels
doivent venir de sources actuelles : SEC/OCC/IRS/Treasury, filings, données IBKR, surface IV, coûts,
liquidité, marge et corporate actions.

La matrice `STRATEGY_READINESS_MATRIX.md` classe les familles de stratégies. Verdict : le corpus est
prêt pour un scanner explicatif en lecture seule ; il n'est pas prêt pour l'envoi ou la recommandation
d'ordres réels.

Avant de coder une stratégie ou d'envoyer un ordre, il reste à :

1. poursuivre la revue sémantique au-delà des dix règles normalisées ;
2. transformer chaque principe en hypothèse testable ;
3. définir les métriques et seuils avec données actuelles ;
4. valider coûts, liquidité, corporate actions et règles IBKR ;
5. backtester hors échantillon puis paper-trader ;
6. obtenir une validation explicite avant toute exécution réelle.
