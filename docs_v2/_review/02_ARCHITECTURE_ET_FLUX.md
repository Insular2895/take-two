# Architecture et flux

## Vue générale

```text
Sources et configuration
        |
        v
Provider read-only -> LiveOptionChainSnapshot -> MarketSnapshot canonique
                                                |
                                                v
Connaissance structurée -> candidats -> économie/pricing -> simulations P et Q
                                                |
                                                v
                            hard gates -> Pareto -> score explicatif
                                                |
                                                v
                                  verdict + rapport + preview bloquée
```

## Pipeline canonique

Le pipeline actif suit cette séquence :

```text
snapshot normalisé
  -> génération exhaustive bornée
  -> pruning structurel
  -> économie canonique
  -> simulation conditionnelle
  -> risque et éligibilité
  -> vetoes
  -> Pareto
  -> ranking explicatif
  -> validation
  -> verdict et rapport
```

Les anciens moteurs `engine.py` et `scoring.py` ont été supprimés. Cette suppression évite qu’un
ancien calcul continue de piloter une décision dans un coin du système.

## Frontière provider

Le cœur quantitatif ne reçoit jamais d’objet `ibapi`. Le transport IBKR transforme les callbacks
en objets bruts internes. Le provider applique gouvernance, retry, pacing, cache et validation.
Enfin, un traducteur produit le contrat provider-neutral consommé par le moteur.

```text
IB Gateway
   |
   | callbacks officiels
   v
OfficialIbkrReadOnlyTransport
   |
   | RawIbkrChainSnapshot
   v
IbkrReadOnlyMarketDataProvider
   |
   | LiveOptionChainSnapshot
   v
live_chain_to_market_snapshot
   |
   | MarketSnapshot
   v
Moteur canonique
```

Cette séparation apporte :

- des tests sans réseau ;
- l’absence de types broker dans le pricing ;
- la possibilité de changer de transport sans modifier les modèles ;
- un endroit unique pour les gates de licence et de fraîcheur ;
- une frontière claire entre données et exécution.

## Flux Cloudflare/Oracle

```text
IB Gateway localhost:4002
        |
        v
Adapter télémétrie Oracle --HTTPS sortant signé--> Cloudflare Worker
                                                     |
                                                     v
                                              D1 latest-only + audit
                                                     |
                                                     v
                                                 Dashboard
```

Le port `4002` n’est pas exposé à Internet. Cloudflare n’ouvre pas une connexion vers la VM : la
VM publie vers Cloudflare. Le credential de télémétrie ne peut pas réclamer un intent paper.

## Pourquoi un monolithe Python modulaire ?

Le domaine est complexe, mais le volume opérationnel actuel ne justifie pas des microservices pour
chaque calcul. Des modules séparés donnent des responsabilités lisibles, tandis qu’un pipeline
canonique évite la divergence des formules et de la vérité économique.

