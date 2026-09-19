# Plan de paper trading

Statut au 19 septembre 2026 : `paper_adapter_ready_offline_runtime_disabled`. Aucune campagne paper n’a été
réalisée. Le plan reste `draft_to_validate` jusqu'à validation du responsable risque.

Blocage actuel : le handshake IBKR paper a été observé le 25 août, mais le nouveau provider de
chaîne n'a pas encore été validé en session réelle ; abonnement/licence OPRA non confirmés,
échantillon historique sous le minimum formel et gate walk-forward non franchi. La campagne ne
doit pas être simulée à partir des mêmes données historiques.

## Prérequis

- gates historique et walk-forward approuvés ;
- flux autorisé et fiable, quotes combo et timestamps ;
- stratégie/politique gelée, seuils et univers prédéfinis ;
- journal immuable des décisions et des changements ;
- séparation stricte entre paper et toute capacité d’ordre réel.

## Contrôle déjà codé hors ligne

- manifeste strict avec période, seuils humains et hashes de lignée ;
- approbation impossible tant que droits data, responsable risque, preuve IBKR et holdout manquent ;
- décisions figées avant résultat dans un journal append-only hash-chaîné ;
- réalisations futures dans un second journal hash-chaîné, liées au hash exact de la décision ;
- refus d'une entrée antidatée, d'un doublon, d'une rupture de chaîne ou d'un drift commit/config ;
- rapport de progression qui ne peut jamais déclarer la validation paper automatiquement.

Le modèle se trouve dans `configs/paper/shadow_campaign.example.json`. Il reste
`example_only=true`. `ttwo-options paper shadow-status` l'analyse sans ouvrir de connexion et sans
démarrer la campagne.

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

## Premier test contrôlé futur

Le runbook est désormais préparé, mais non exécuté. Le premier test sera TTWO uniquement, quantité
représentative minimale, un seul BAG LMT, pendant les heures liquides, avec données live, tick
`reqMarketRule` valide, structure simple, client ID dédié, aucune session concurrente, logs API
Detail, aucune protection/ladder automatique et kill switch testé avant l’ouverture de fenêtre.

Les résultats seront séparés en : chemin système, fill du simulateur Paper et exécutabilité Live
(`NOT_PROVEN_BY_PAPER_ALONE`). Tout reprice nécessitera marché frais, ticket quantitatif complet et
nouvelle confirmation humaine.
