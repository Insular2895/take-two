# Architecture - TTWO options opportunity engine V8

Statut : `source_backed_screen_grade_no_trade`

## Objectif

V8 transforme le panel V7 en atelier d'opportunites read-only. Il compare des architectures
explicites, backteste les sorties conditionnelles sur la trajectoire EOD, normalise les credits par
leur risque borne et separe ce qui est backteste, seulement documente ou interdit par risque.

## Couches

```text
registre de 21 architectures
        |
        +--> backtested: 13 structures autonomes a risque borne
        +--> catalog_only: portefeuille ou donnees intraday requis
        +--> risk_disabled: short gamma nu ou ratio ambigu
        |
        v
sessions/closes Alpaca + taux Treasury + evenements declares
        |
        v
signal MarketData.app --> selection delta/moneyness/ailes/terme
        |
        v
entree EOD --> premieres marques TP/SL --> sortie temps
        |
        v
P&L executable, capital a risque, IV/RV, stress, Wilson/bootstrap/DSR
        |
        v
test + holdout gouverne + chaine actuelle --> eligible/watchlist/blocked/no_trade
        |
        v
rapport JSON/Markdown + dashboard portable
```

## Architectures

Backtestees : long call/put, bull call/bear put spreads, long straddle/strangle, call/put
butterflies, iron condor, long call calendar, call diagonal, LEAPS call/put.

Catalogue seulement : protective put, covered call, collar/fence et gamma scalping. Ces structures
ont besoin de positions, lots, cout fiscal ou donnees intraday qui ne sont pas disponibles.

Desactivees par risque : short straddle, short strangle, ratio spread et ratio backspread generique.
Le nom d'un ratio ne suffit pas a prouver que sa perte est bornee.

## Regles d'execution historique

- Chaque jambe conserve side, option type, strike, echeance et quantite.
- Un butterfly est `long 1 / short 2 / long 1` a une echeance.
- Un iron condor achete les ailes et vend les deux options interieures ; son denominator est la
  perte terminale maximale, pas le credit recu.
- Calendar et diagonal ont une echeance arriere longue et une echeance avant qui doit rester apres
  la sortie planifiee.
- Une cible de moneyness rejette tout strike situe a plus de cinq points de pourcentage de la
  recette; le contrat n'est pas remplace silencieusement par le strike disponible le moins eloigne.
- TP/SL est mesure sur la premiere marque EOD complete, avec les cotes executables de toutes les
  jambes et les couts aller-retour. La marque exacte est conservee, elle n'est pas plafonnee au TP.

## Gouvernance holdout

Le holdout observe en V7 n'est plus vierge. V8 le declare `reused_exploratory`; meme une variante
qui passerait les gates numeriques ne pourrait obtenir que `watchlist`. Une future campagne doit
figer une nouvelle periode avant de consulter les resultats pour autoriser `eligible`.

## Premier run reel

- Donnees backtest : 2025-07-21 au 2026-07-17 ; scan actuel MarketData.app au 2026-07-16.
- 4 panels, 17 variantes configurees dont 13 structures optionnelles, 81 fenetres ; 12 variantes
  optionnelles conservent des metriques test apres le controle strict de moneyness.
- 977 requetes logiques au run final, 975 cache hits.
- 13 candidats actuels `blocked`, zero `eligible`, zero `watchlist`; classement `no_trade`.
- Lead suffisamment observe : long call 150 DTE/delta 55, test n=11, taux de gain 54.5 %
  [28.0 %, 78.7 %], mediane +3.02 %, CVaR 35.65 % et drawdown 89.49 % ; holdout mediane
  -15.09 % et drawdown 94.23 %.
- Recette put `K+10/365d/TP80/SL50/H30` : aucune observation conforme apres application de la
  tolerance de cinq points. Le snapshot actuel ne contient pas de put cote assez proche de la
  cible ; la recette reste testable, mais sa performance n'est pas estimee.
- Un LEAPS call historique a touche SL50 ; les trois autres cas sont sortis au temps. Ces
  observations valident la mecanique de sortie, pas la strategie.

## Dashboard

Le HTML autonome place d'abord les opportunites actuelles avec raisons de blocage, ticket IBKR en
langage clair, scenario de gain et KPI, puis les gagnants historiques et les 21 architectures. Le
ticket distingue prix d'option par action et cout indicatif d'un lot de 100, tout en rappelant que
la limite doit venir de la cotation IBKR live. Les tables d'audit et jambes restent en dessous. Le
packaging canonique valide sources, interaction et absence de debordement a 1440 et 390 pixels.

## Sources

- Corpus local : Natenberg chapitre 8, McMillan butterfly/LEAPS et matrice documentaire V8.
- OCC/OIC : `https://www.optionseducation.org/strategies/all-strategies-en` et
  `https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document`.
- IBKR : `https://www.ibkrguides.com/traderworkstation/create-a-combination-order.htm` et
  `https://www.ibkrguides.com/traderworkstation/using-the-combo-trader.htm`.
- Donnees : Alpaca sessions/chaines, MarketData.app EOD bid/ask, US Treasury par yields.

Ces sources documentent les structures et risques. Elles ne valident ni les parametres V8 ni une
decision d'investissement.
