# Strategie de tests V9

La suite est offline, déterministe et sans broker :

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

Les tests couvrent :

- payoff call/put/vertical, max gain/perte, break-even et débit exécutable ;
- bid/ask, commissions, slippage et multiplicateur non standard ;
- monotonie call/put et bornes des verticals sur une grille de spots ;
- agrégation des Greeks ;
- dominance numerique americain/europeen, dividendes discrets, assignment et pin risk ;
- interpolation/extrapolation de surface IV et veto de fraicheur ;
- reproductibilite GBM/Merton/Heston, variance non negative et comportement de queue ;
- scénarios gap, IV crush/expansion, délai, ex-dividende et liquidité ;
- reconciliation de l'attribution par repricing jusqu'au P&L ;
- calibration RV/jumps, refus Heston sur preuve insuffisante et exclusion temporelle ;
- backtest bid/ask, frais, train/test, drawdown et rejet du look-ahead ;
- credentials Alpaca absents/redactes, normalisation de bars, provenance source-backed ;
- conversion bars actions vers calibration et bars options vers proxy explicite ;
- normalisation de chaine Alpaca avec quote, IV et Greeks ;
- credentials MarketData.app absents/redactes et token limite au header Authorization ;
- normalisation des chaines EOD, verification de session, symbole OCC et tableaux alignes ;
- cache MarketData.app SHA-256, cache hit et blocage sur corruption ;
- recalcul IV/Greeks americains QuantLib depuis un midpoint EOD ;
- conversion EOD bid/ask vers backtest, open interest conserve et readiness `screen_grade` ;
- panel MarketData.app a signal anterieur, selection delta/liquidite, spreads bornes, veto de risque
  et reference `no_trade` ;
- contrainte de risque EUR appliquee au scan actuel et aux cas historiques avant calcul des KPI ;
- generation de sessions non chevauchantes avec splits train/test/holdout, embargo, expiration
  cotee proche du DTE cible et taux Treasury interpole sans look-ahead ;
- intervalles Wilson et bootstrap deterministes, volatilite/downside, profit factor, VaR/CVaR et
  approximation Deflated Sharpe ;
- P&L par jambe aux cotes executables, couts, stress spread/slippage et KPI par trade ;
- orchestration multi-horizon/multi-DTE, cache memoire, scan de chaine actuelle et maintien de
  `no_trade` lorsque les gates test/holdout echouent ;
- generation de l'artefact canonique du dashboard et libelles compacts auditables ;
- registre d'architectures avec separation `backtested`, `catalog_only` et `risk_disabled` ;
- jambes multi-quantites, butterflies 1/-2/1, iron condor et term spreads multi-echeances ;
- selection moneyness `spot +/-10 %`, capital a risque des credits et rejet du risque non borne ;
- premiere sortie EOD franchissant TP/SL, motif de sortie et date effective auditables ;
- regime momentum/volatilite sans look-ahead, ratio IV/RV et verrou `reused_exploratory` ;
- datasets dedies aux opportunites actuelles, gagnants historiques et bibliotheque d'architectures ;
- veto fraîcheur, quote, contrat ajusté, marge, événement, catalyseur, evidence et risque non borné ;
- sérialisation JSON/Markdown/journal et absence de statut d'exécution ;
- submit/modify/cancel bloqués par `ForbiddenOperation`.

Les tests ne valident pas un prix de marché, une volatilité future ou une stratégie d'investissement.
Ils valident la mécanique et les garde-fous du logiciel.

Etat verifie le 2026-07-19 : 68 tests, Ruff, mypy strict et `pip check` passent localement. Le SDK
Alpaca emet un warning de deprecation interne `websockets.legacy` sous Python 3.14.
