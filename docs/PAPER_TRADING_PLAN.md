# Plan de paper trading

Statut au 18 août 2026 : `blocked_before_start`. Aucune campagne paper n’a été
réalisée. Le plan reste `draft_to_validate` jusqu'à validation du responsable risque.

Blocage actuel : session IBKR paper non connectée, abonnement/licence OPRA non
confirmés, échantillon historique sous le minimum formel et gate walk-forward non
franchi. La campagne ne doit pas être simulée à partir des mêmes données historiques.

## Prérequis

- gates historique et walk-forward approuvés ;
- flux autorisé et fiable, quotes combo et timestamps ;
- stratégie/politique gelée, seuils et univers prédéfinis ;
- journal immuable des décisions et des changements ;
- séparation stricte entre paper et toute capacité d’ordre réel.

## Mesures

- décision, quote observée, limite, remplissage simulé et temps de latence ;
- slippage, commissions, marge what-if et écarts combo/synthétique ;
- partial fills, rejets, annulations et données manquantes ;
- P&L prudent, drawdown, VaR/CVaR, turnover et capacité `NO_TRADE` ;
- dérive de calibration, stabilité des rangs et incidents de données.

## Sortie

La durée, la taille minimale, les seuils d’erreur et les limites de perte sont à
valider par le responsable risque. Le résultat doit inclure échecs et périodes sans
trade. Une campagne paper ne déverrouille pas l’exécution dans cette version.
