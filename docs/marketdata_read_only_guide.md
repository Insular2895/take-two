# Guide MarketData.app read-only

## Role

MarketData.app complete Alpaca pour les backtests options EOD. Le connecteur ne charge que des
donnees de marche historiques et ne contient aucun client broker, compte, portefeuille, ordre,
exercise ou position.

Le plan gratuit officiel annonce :

- 100 credits API par jour ;
- un an d'historique ;
- options retardees de 24 heures ;
- chaines historiques facturees par tranche de 1 000 contrats retournes ;
- usage individuel, personnel et non commercial.

Sources officielles :

- [pricing](https://www.marketdata.app/pricing/) ;
- [option-chain endpoint](https://www.marketdata.app/docs/api/options/chain/) ;
- [plan limits](https://www.marketdata.app/docs/account/plan-limits/) ;
- [data freshness](https://www.marketdata.app/docs/account/data-freshness/) ;
- [terms of service](https://www.marketdata.app/terms/).

## Configuration

Creer un compte gratuit, puis conserver le token uniquement dans un `.env` local :

```bash
MARKETDATA_TOKEN=...
```

Le token n'est accepte ni en argument CLI, ni dans un fichier de specification, ni dans les logs.

```bash
set -a
source .env
set +a
```

## Chaine historique EOD

Une requete filtree limite les credits consommes :

```bash
.venv/bin/ttwo-options marketdata-chain \
  --ticker TTWO \
  --date 2026-07-17 \
  --expiration 2026-11-20 \
  --side call \
  --strikes 220,240,260 \
  --risk-free-rate 0.04 \
  --json-out data/marketdata/ttwo_2026-07-17_calls.json
```

Champs conserves :

- symbole OCC, expiration, type et strike ;
- timestamp reel de la quote EOD ;
- bid, ask, tailles, midpoint et last ;
- volume, open interest et prix du sous-jacent ;
- IV/Greeks fournisseur lorsqu'ils existent ;
- IV/Greeks QuantLib calcules depuis le midpoint lorsque `--risk-free-rate` est fourni ;
- provenance, date de collecte, cache et en-tetes de credits.

Une date retournee differente de la date demandee, un tableau mal aligne ou une quote croisee est
bloquant. L'API n'est pas autorisee a substituer silencieusement une session precedente.

## IV et Greeks locaux

Les tests publics du 2026-07-19 ont renvoye des IV/Greeks nuls sur les dates historiques. Le moteur
resout donc l'IV du midpoint par bissection autour du pricer americain QuantLib, puis calcule delta,
gamma, theta, vega et rho par differences finies.

Le taux sans risque est une entree explicite. `0.04` dans les exemples est illustratif et doit etre
remplace par un taux source-backed coherent avec la date historique. Le dividend yield vaut zero
par defaut dans la commande de chaine ; les dividendes discrets doivent etre fournis dans une
specification de backtest lorsqu'ils sont applicables.

## Backtest EOD

Le fichier d'exemple est :

`fixtures/marketdata_tt_options_backtest_spec.example.json`

Chaque jambe contient un symbole OCC et un multiplicateur explicite. Le connecteur extrait
l'expiration, le type et le strike du symbole, groupe les requetes par session et filtre la chaine
cote serveur.

```bash
.venv/bin/ttwo-options marketdata-backtest \
  --spec fixtures/marketdata_tt_options_backtest_spec.example.json \
  --dataset-out data/marketdata/ttwo_eod_backtest_dataset.json \
  --json-out reports/marketdata_tt_options_backtest.json \
  --markdown-out reports/marketdata_tt_options_backtest.md
```

Le backtest achete a l'ask, revend au bid, ajoute commissions et slippage, et rejette toute quote
connue apres la decision declaree. Sa qualite de prix est `historical_eod_bid_ask` et sa readiness
reste `screen_grade` : il ne reconstitue ni les quotes intraday, ni le market impact, ni une combo
quote executable.

## Panel walk-forward

Le panel V1 compare `no_trade`, long call, bull call spread, long put et bear put spread sur une
expiration commune. Pour chaque observation, il :

1. selectionne les contrats sur une chaine EOD de signal ;
2. exige une seance d'entree ulterieure ;
3. execute les longs a l'ask et les shorts au bid ;
4. sort sur une troisieme seance au cote executable oppose ;
5. separe chronologiquement train et test ;
6. applique les seuils minimaux d'observations/couverture et les veto de rendement, drawdown,
   pire perte et stabilite avant classement.

```bash
.venv/bin/ttwo-options marketdata-panel \
  --spec fixtures/marketdata_tt_options_panel_v1.json \
  --json-out reports/marketdata_tt_options_panel_v1.json \
  --markdown-out reports/marketdata_tt_options_panel_v1.md
```

Premier run TTWO du 2026-07-19 : 10 observations, 6 train et 4 test. `no_trade` est la seule
strategie ayant passe les veto. Le long call etait le meilleur comparatif optionnel sur la mediane
test (`+4.47 %`), mais a ete bloque par un drawdown test de `49.11 %` et une pire perte de
`-41.60 %`. Ce resultat est un screening initial, pas une conclusion statistique ni une
recommandation.

## Cache

Les reponses brutes sont stockees sous `data/marketdata/cache/`, ignore par Git. La cle de cache
depend de l'endpoint et des filtres, et le contenu JSON est controle par SHA-256 avant reutilisation.
Une corruption bloque le run. `--force-refresh` renouvelle explicitement une entree.

Le cache ne contient jamais le token. Les conditions fournisseur exigent aussi le respect des
regles de conservation et la suppression des donnees lorsque le droit d'usage prend fin.

## Limites

- un an seulement sur le plan gratuit ;
- 100 credits par jour ;
- pas de NBBO intraday historique ;
- pas de multiplicateur ou deliverable broker/OCC dans la quote ;
- pas de marge, commissions broker, borrow ou combo quotes ;
- usage personnel/non commercial uniquement ;
- aucune capacite d'ordre.
- dix observations seulement dans le premier panel, dont quatre hors echantillon ;
- selection delta dependante du taux, des dividendes et du moteur QuantLib ;
- prix de jambes separes, sans garantie de combo fill simultane.
