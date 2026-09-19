# Moteur quantitatif expliqué

## Construction des candidats

Le moteur énumère les structures permises à partir des options réellement présentes dans le
snapshot. Il applique d’abord les contraintes structurelles : ordre des strikes, expirations,
ratios, horizon, budget, liquidité et risque borné.

Les principales architectures couvertes incluent long call/put, verticales, butterflies,
calendars, diagonales, straddle, strangle et iron condor. Certaines structures restent
`catalog_only` ou `risk_disabled` lorsque leur risque ou leur maintenance ne sont pas prouvés.

## Prix et économie

Le chemin canonique transporte explicitement :

- spot et volatilité ;
- taux et dividendes ;
- temps exact ;
- style américain/européen ;
- multiplicateur et ajustement ;
- côtés exécutables bid/ask ;
- frais, slippage, FX et coûts de lifecycle.

Le P&L net suit une équation exact-once :

```text
P&L brut
- coût bid/ask entrée
- coût bid/ask sortie
- slippage entrée/sortie
- commissions
- exercice/assignation/settlement
- FX
= P&L net
```

Un composant requis inconnu rend le P&L net inconnu ; il ne devient pas zéro.

## Mesures P et Q

- `Q/RISK_NEUTRAL` sert au pricing et aux Greeks.
- `P/REAL_WORLD` sert aux probabilités et au P&L espéré.

Un modèle Q ou un stress non calibré peut apparaître comme diagnostic, mais ne peut pas piloter
EV, probabilité de perte, Pareto ou verdict. Sans modèle P éligible, le résultat décisionnel est
`BLOCKED`.

## Validation

Les tests unitaires prouvent les formules et invariants logiciels. Ils ne prouvent pas la
performance. La progression attendue est :

```text
tests -> historique autorisé -> calibration -> walk-forward -> holdout -> shadow -> paper
```

Le holdout final n’est ouvert qu’une fois après les gates précédents. Les anciens holdouts V7–V9
sont contaminés et ne peuvent plus promouvoir une stratégie.

## Pourquoi Pareto avant le score ?

Le risque, le rendement, les coûts, la robustesse et la qualité d’exécution ne se réduisent pas
naturellement à un chiffre unique. Pareto conserve les compromis non dominés. Le score final sert à
expliquer et ordonner secondairement ; il ne peut pas annuler un veto.

