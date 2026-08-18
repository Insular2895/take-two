# Calibration historique hors ligne

Le module `intelligence.calibration` importe JSON, CSV et, si pandas/pyarrow sont
installés, Parquet. Il fonctionne sans réseau et ne substitue jamais une fixture à un
dataset manquant.

## Contrat du dataset

Le dataset porte une version, un cutoff, une timezone, un fournisseur, les droits
d’usage, les politiques de splits/dividendes et un indicateur `synthetic`. Chaque
observation porte `timestamp` et `available_at`. Une quote option exige symbole,
expiration, strike, type, bid et ask cohérents.

Les contrôles couvrent :

- disponibilité point-in-time et exclusion post-cutoff ;
- timezone, unités, bid/ask et identité du contrat ;
- doublons, hash du dataset et nombre d’observations ;
- séparation entre données synthétiques et données autorisées.

## Commandes

```bash
ttwo-options calibration validate-dataset --dataset PATH
ttwo-options calibration build-splits --dataset PATH --method expanding
ttwo-options calibration fit --dataset PATH
ttwo-options calibration report --dataset PATH --walk-forward PATH
```

Sans `--dataset`, le statut est `BLOCKED_MISSING_CALIBRATION_DATA`. Sur la fixture
fournie, il est `FIXTURE_ONLY_NOT_CALIBRATED`.

## Modèles

- GBM : drift et volatilité annualisés à partir des log-rendements.
- Local volatility : seulement si plusieurs surfaces et strikes sont présents ;
  les contrôles d’arbitrage restent obligatoires.
- Heston : aucun faux fit à partir des seuls closes ; un historique de surfaces et un
  optimiseur contraint sont requis.
- Sauts : fréquence, direction et amplitude sont séparées ; le résultat reste
  expérimental jusqu’au walk-forward.

Un fit in-sample est toujours `pending_validation`, jamais une promotion.
