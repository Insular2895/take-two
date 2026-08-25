# Architecture - TTWO options research engine V2

Statut : `implemented_v2_screen_grade_to_validate`

## Flux

```text
fixture sourcee et horodatee
        |
        v
contrats Pydantic + fraicheur + provenance
        |
        +--> surface IV --> interpolation strike/expiration
        |
        +--> dividendes --> QuantLib finite differences americain
        |
        +--> GBM / Merton / Heston full truncation
        |
        v
repricing sequentiel spot/temps/IV/taux/couts + residuel
        |
        v
veto, assignment/pin flags, score, front de Pareto
        |
        v
rapport JSON/Markdown/journal `screen_grade`
```

La calibration et le backtest utilisent des contrats et commandes separes. Cette separation
empeche une fixture de prix courante de se presenter implicitement comme preuve historique.

## Modules V2

- `american.py` : moteur QuantLib `FdBlackScholesVanillaEngine`, exercice americain, dividendes
  discrets, benchmark europeen, Greeks par differences finies et risque assignment/pin.
- `vol_surface.py` : interpolation lineaire strike puis expiration, extrapolation visible et
  fallback vers IV de quote/RV.
- `simulation.py` : GBM exact terminal, Merton compound-Poisson et Heston full-truncation Euler.
- `scenarios.py` : repricing americain et attribution sequentielle reconcilee au P&L.
- `calibration.py` : RV close-to-close, detection de jumps heuristique et refus Heston lorsque les
  donnees de variance/surface historique manquent.
- `backtesting.py` : bid/ask executable, frais aller-retour, splits train/test, drawdown et veto
  look-ahead.

## Frontieres de modele

1. Le prix americain est un resultat numerique, pas un prix executable.
2. Le benchmark europeen utilise les memes taux, volatilite et dividendes pour isoler la prime
   d'exercice anticipe.
3. Les niveaux assignment/pin sont des drapeaux deterministes, jamais des probabilites.
4. L'attribution depend de l'ordre spot, temps, volatilite, taux, couts; le residuel reste visible.
5. Merton et Heston ne deviennent pas calibres parce qu'ils produisent des chemins valides.
6. Un backtest synthetique prouve les calculs et controles temporels uniquement.
7. `screen_grade` ne peut pas autoriser un ordre, une taille ou une recommandation.

## Passage vers une validation empirique

Il faut fournir une histoire TTWO horodatee de spot et de chaines options, des surfaces IV
reconstructibles sans look-ahead, des dividendes/corporate actions, les couts broker et les combo
quotes. La calibration doit etre figee avant chaque entree test. Les resultats train et test
doivent rester separes et la robustesse doit etre verifiee sur plusieurs regimes et seuils.

## References techniques

- Cox, Ross et Rubinstein (1979), *Option Pricing: A Simplified Approach*.
- Merton (1976), *Option Pricing When Underlying Stock Returns Are Discontinuous*.
- Heston (1993), *A Closed-Form Solution for Options with Stochastic Volatility*.
- QuantLib 1.43, moteur finite-difference Black-Scholes.
- OCC, documentation officielle sur exercice et assignment des options actions americaines.
