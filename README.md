# take-two

Base documentaire et pack de recherche pour étudier Take-Two et concevoir, dans une phase
ultérieure, un outil d'analyse de structures optionnelles.

Le point d'entrée principal est [option-research-engine/README.md](option-research-engine/README.md).

Le dépôt ne contient pas les PDF originaux. Les livres restent locaux, en lecture seule, et seules
leurs extractions traçables, règles candidates, preuves légères et métadonnées peuvent être
versionnées.

## Moteur TTWO options V2

La V2 exécutable est un moteur de recherche **read-only**. Elle compare `no-trade`, action,
achat de call, achat de put et verticals bornés, price les options américaines avec QuantLib,
interpole une surface IV explicite et compare GBM, jump diffusion de Merton et volatilité
stochastique de type Heston. Elle ne contient aucune capacité d'envoi, de modification ou
d'annulation d'ordre.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/ttwo-options analyze \
  --fixture fixtures/ttwo_v2_fixture.json \
  --json-out reports/ttwo_v2_decision_report.json \
  --markdown-out reports/ttwo_v2_decision_report.md \
  --journal-out reports/ttwo_v2_decision_journal.md

.venv/bin/ttwo-options calibrate \
  --fixture fixtures/ttwo_v2_calibration_fixture.json \
  --json-out reports/ttwo_v2_calibration_report.json \
  --markdown-out reports/ttwo_v2_calibration_report.md

.venv/bin/ttwo-options backtest \
  --fixture fixtures/ttwo_v2_backtest_fixture.json \
  --json-out reports/ttwo_v2_backtest_report.json \
  --markdown-out reports/ttwo_v2_backtest_report.md
```

Les trois fixtures V2 sont synthétiques. Elles valident le logiciel, pas TTWO ni une stratégie.
Les rapports restent donc `screen_grade` et interdisent toute capacité d'ordre.

## Donnees reelles Alpaca

La V3 ajoute un adaptateur Alpaca strictement read-only pour la chaine options actuelle, les bars
actions de calibration et les bars options historiques. Les cles restent dans l'environnement et
aucun client d'ordres Alpaca n'est importe.

```bash
set -a && source .env && set +a
.venv/bin/ttwo-options alpaca-check --ticker TTWO --stock-feed iex
.venv/bin/ttwo-options alpaca-chain --ticker TTWO --feed indicative \
  --json-out data/alpaca/ttwo_option_chain.json
```

Voir le [guide Alpaca read-only](docs/alpaca_read_only_guide.md) pour la calibration et le
backtest. L'historique options Alpaca commence en fevrier 2024 et les barres historiques ne sont
pas des quotes NBBO ; les backtests correspondants restent `screen_grade`.

## Chaines EOD historiques MarketData.app

La V4 complete Alpaca avec les chaines options historiques EOD de MarketData.app. Elle conserve
bid/ask, tailles, volume, open interest, sous-jacent et timestamps, recalcule localement IV et
Greeks americains avec QuantLib et met en cache les reponses brutes avec controle d'integrite.

```bash
set -a && source .env && set +a
.venv/bin/ttwo-options marketdata-chain \
  --ticker TTWO \
  --date 2026-07-16 \
  --expiration 2026-11-20 \
  --side call \
  --strike-limit 10 \
  --risk-free-rate 0.04 \
  --json-out data/marketdata/ttwo_2026-07-17_chain.json

.venv/bin/ttwo-options marketdata-backtest \
  --spec fixtures/marketdata_tt_options_backtest_spec.example.json \
  --dataset-out data/marketdata/ttwo_eod_backtest_dataset.json \
  --json-out reports/marketdata_tt_options_backtest.json \
  --markdown-out reports/marketdata_tt_options_backtest.md

.venv/bin/ttwo-options marketdata-panel \
  --spec fixtures/marketdata_tt_options_panel_v1.json \
  --json-out reports/marketdata_tt_options_panel_v1.json \
  --markdown-out reports/marketdata_tt_options_panel_v1.md
```

Voir le [guide MarketData.app read-only](docs/marketdata_read_only_guide.md). Le plan gratuit est
limite a un usage personnel/non commercial, a un an d'historique et a 100 credits par jour. Les
prix restent `historical_eod_bid_ask`, jamais presentes comme un replay NBBO intraday. Le panel
selectionne les contrats sur une seance anterieure a l'entree, conserve `no_trade` comme reference
et applique les veto de rendement, drawdown, pire perte, stabilite et couverture avant classement.

## Precision, holdout et dashboard V7

La V7 genere des observations non chevauchantes, separe `train`, `test` et `holdout`, applique un
embargo temporel, choisit une expiration reellement cotee proche du DTE cible et interpole le taux
sans risque depuis les courbes officielles du Treasury. Elle mesure notamment l'intervalle Wilson
du taux de gain, les intervalles bootstrap, volatilite, downside deviation, VaR/CVaR, drawdown,
profit factor, stress de spread/slippage et Deflated Sharpe.

```bash
set -a && source .env && set +a

.venv/bin/ttwo-options accuracy-spec \
  --config fixtures/marketdata_tt_options_accuracy_v7_generator.json \
  --calibration-dataset data/alpaca/ttwo_calibration_dataset_2026-07-19.json \
  --current-chain data/alpaca/ttwo_option_chain_2026-07-19.json \
  --json-out data/marketdata/ttwo_v7_accuracy_spec.json

.venv/bin/ttwo-options marketdata-accuracy \
  --spec data/marketdata/ttwo_v7_accuracy_spec.json \
  --json-out reports/ttwo_v7_accuracy_report.json \
  --markdown-out reports/ttwo_v7_accuracy_report.md \
  --artifact-out reports/ttwo_v7_accuracy_dashboard.artifact.json

.venv/bin/ttwo-options accuracy-dashboard \
  --report reports/ttwo_v7_accuracy_report.json \
  --artifact-out reports/ttwo_v7_accuracy_dashboard.artifact.json
```

Le dashboard portable final est
[reports/ttwo_v7_accuracy_dashboard.html](reports/ttwo_v7_accuracy_dashboard.html). Il filtre les
trades gagnants/perdants par strategie, echantillon et regime, puis expose les KPI de chaque trade
et de chaque jambe. Le premier run V7 conserve `no_trade`: aucune variante ni aucun candidat
actuel ne franchit tous les gates test, holdout et risque.

## Budget EUR 1 000 et horizons V9

La V9 ajoute une contrainte dure de risque en euros au scan actuel et a chaque cas historique.
Elle compare deux plans de recherche, sans capacite d'ordre :

- `single_long` : une poche de EUR 1 000 sur un vertical call longue echeance ;
- `staged_three` : EUR 310 court, EUR 245 moyen et EUR 445 long.

Le change utilise pour ce run est `1 EUR = 1.1435 USD`, reference BCE du 2026-07-17. Le prix
limite reel, le change applique et les frais doivent toujours etre reverifies dans IBKR. La chaine
actuelle ne cote pas une echeance a un an : la maturite la plus lointaine disponible est le
2027-03-19, soit 246 jours depuis la seance EOD du 2026-07-16.

```bash
set -a && source .env && set +a

.venv/bin/ttwo-options accuracy-spec \
  --config fixtures/marketdata_tt_options_budget_v9_generator.json \
  --calibration-dataset data/alpaca/ttwo_calibration_dataset_2026-07-19.json \
  --current-chain data/alpaca/ttwo_option_chain_2026-07-19.json \
  --json-out data/marketdata/ttwo_v9_budget_spec.json

.venv/bin/ttwo-options marketdata-accuracy \
  --spec data/marketdata/ttwo_v9_budget_spec.json \
  --json-out reports/ttwo_v9_budget_report.json \
  --markdown-out reports/ttwo_v9_budget_report.md \
  --artifact-out reports/ttwo_v9_budget_dashboard.artifact.json
```

Le dashboard final est
[reports/ttwo_v9_budget_dashboard.html](reports/ttwo_v9_budget_dashboard.html). Il place d'abord
la comparaison des plans, puis les tickets IBKR lisibles, les raisons de blocage, les scenarios de
gain, les KPI historiques et la bibliotheque d'architectures. Le run V9 conserve `no_trade` : le
plan trois temps n'a qu'une poche actuellement construisible et aucun des deux plans n'est valide
par un echantillon historique et un holdout suffisants.

Voir aussi [l'architecture V9](docs/architecture/ttwo_options_budget_engine_v9.md).

## Panel d'architectures et opportunites V8

La V8 ajoute un registre de 21 architectures. Treize structures autonomes a risque borne entrent
dans le panel : options longues, verticals, straddle/strangle longs, butterflies, iron condor,
calendar/diagonal calls et recettes LEAPS. Les protective puts, covered calls, collars et le gamma
scalping restent `catalog_only` faute de portefeuille ou de donnees intraday. Les straddles/strangles
shorts et ratios ambigus restent `risk_disabled`.

Les jambes ont des quantites explicites, les credits sont normalises par leur perte maximale et les
sorties `profit target / stop / time` sont recherchees sur les cotes EOD successives. La recette
`leaps_put_h30_dte365_tp80` vise un put proche de `spot +10 %`, controle chaque semaine, cash-out a
`+80 %`, stop a `-50 %`, sinon sort apres 30 seances. Si aucun strike cote n'est a moins de cinq
points de pourcentage de la cible, la selection est bloquee au lieu d'utiliser un faux equivalent.

```bash
set -a && source .env && set +a

.venv/bin/ttwo-options accuracy-spec \
  --config fixtures/marketdata_tt_options_opportunity_v8_generator.json \
  --calibration-dataset data/alpaca/ttwo_calibration_dataset_2026-07-19.json \
  --current-chain data/alpaca/ttwo_option_chain_2026-07-19.json \
  --json-out data/marketdata/ttwo_v8_opportunity_spec.json

.venv/bin/ttwo-options marketdata-accuracy \
  --spec data/marketdata/ttwo_v8_opportunity_spec.json \
  --json-out reports/ttwo_v8_opportunity_report.json \
  --markdown-out reports/ttwo_v8_opportunity_report.md \
  --artifact-out reports/ttwo_v8_opportunity_dashboard.artifact.json
```

Le dashboard final est
[reports/ttwo_v8_opportunity_dashboard.html](reports/ttwo_v8_opportunity_dashboard.html). Sa
premiere table regroupe opportunite, raisons de blocage, jambes exactes, entree/sortie et KPI. Les
instructions sont formulees comme un ticket IBKR lisible : acheter/vendre, call/put, quantite,
strike, echeance, ordre limite debit/credit, prix par action et cout indicatif par lot. Chaque ligne
explique aussi le scenario qui la ferait gagner. Les gagnants historiques et la bibliotheque
complete sont separes. Le run V8 du 2026-07-19 conserve
`no_trade` : 13 candidats actuels sont bloques et aucun n'est eligible. Le holdout est marque
`reused_exploratory`, car il a deja ete consulte pendant V7.

Contrôles de qualité :

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

Documentation technique :

- [architecture V8](docs/architecture/ttwo_options_opportunity_engine_v8.md),
  [architecture V7](docs/architecture/ttwo_options_research_engine_v7.md),
  [architecture V2](docs/architecture/ttwo_options_research_engine_v2.md) et
  [architecture V1](docs/architecture/ttwo_options_research_engine_v1.md) ;
- [ADR de stack](docs/adr/0001-python-read-only-engine.md) et
  [statut des règles](docs/rule_status_policy.md) ;
- [contrats de données](docs/data_contracts/ttwo_options_v1.md) ;
- [guide IBKR read-only](docs/ibkr_read_only_guide.md) ;
- [guide Alpaca read-only](docs/alpaca_read_only_guide.md) ;
- [guide MarketData.app read-only](docs/marketdata_read_only_guide.md) ;
- [fixtures](docs/fixtures_guide.md), [tests](docs/testing_strategy.md) et
  [limites connues](docs/known_limits.md).
