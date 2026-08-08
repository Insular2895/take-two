# Phase M future — plan de validation finale OPRA

Statut actuel : `ADAPTER_READY_NOT_CONNECTED`. La Phase M n'est pas démarrée. Ce plan
n'autorise ni connexion aujourd'hui, ni ordre réel, ni création d'un faux holdout.

## Configuration à fournir

```text
OPRA_PROVIDER=...
OPRA_API_KEY=...
OPRA_API_SECRET=...
OPRA_ACCOUNT_OR_SESSION=...
```

`OPRA_ENDPOINT` est facultatif si le provider sélectionné exige un endpoint distinct.
Les secrets sont chargés comme `SecretStr`, ne sont jamais sérialisés dans un rapport et
ne doivent pas être commités.

Commande de finalisation/contrôle du contrat :

```bash
ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml
```

Cette commande ne se connecte pas et ne démarre pas la Phase M. Elle reconstruit les
preuves agrégées et indique si les variables attendues sont présentes. Le provider réel
implémentera `LiveOptionMarketDataProvider`, limité à `health()` et
`get_option_chain()`.

## Protocole prospectif à exécuter après validation humaine

1. Vérifier entitlement, licence, stockage, redistribution et limites de taux.
2. Capturer la chaîne live, le spot, le bid/ask, les timestamps provider/réception,
   la fraîcheur, le spread, le volume, l'open interest et les Greeks disponibles.
3. Recalculer les métriques lorsque le provider ne les fournit pas, sans masquer leur
   provenance.
4. Geler l'univers de candidats, les cinq scores, les métriques brutes, la
   classification, le candidat sélectionné, la meilleure baseline, le no-position,
   les prédictions et leurs intervalles dans un `PaperDecisionRecord` hash-chaîné.
5. Ne saisir le chemin réalisé qu'ultérieurement dans un `PaperRealizationRecord`
   séparé : entrée paper, sortie paper, slippage, frais, P&L et postmortem.
6. Comparer V10 aux mêmes baselines sur les mêmes timestamps et coûts.
7. Surveiller calibration, Brier/log-loss lorsque définis, rang, CVaR, pertes sévères,
   qualité des fills simulés, rejets, trous de données et changements de régime.
8. Appliquer purge/embargo et ne jamais retuner sur le holdout final après ouverture.
9. Produire un rapport Phase M distinct soumis à validation humaine.

## Critères de blocage immédiat

- entitlement non confirmé ;
- timestamp absent, quote trop vieille ou chaîne incomplète ;
- bid/ask croisé, contrat non standard non traité ou multiplicateur inconnu ;
- frais, slippage ou FX manquants ;
- hash de snapshot/decision invalide ;
- tentative de réécrire une décision après résultat ;
- incapacité à construire les mêmes baselines ;
- toute tentative de submit, modify, cancel, exercise ou roll.

## Invariants permanents

```text
read_only=true
transmit=false
what_if=true
order_capability=forbidden
```

Le preview IBKR peut vérifier contrat, combo, commission et marge what-if si disponible.
Il ne constitue jamais une autorisation de transmission.
