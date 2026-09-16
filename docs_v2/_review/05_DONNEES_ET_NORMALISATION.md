# Données, timestamps et normalisation

## Sources historiques et live

| Source | Usage | Qualité maximale actuelle |
|---|---|---|
| MarketData.app EOD | Historique bid/ask options | `screen_grade` |
| Alpaca IEX/indicative | Spot, bars et contrôle courant | Indicatif selon abonnement |
| Treasury/ECB/SEC/Take-Two | Taux, FX, fondamentaux et événements | Source officielle, avec cutoff |
| IBKR/OPRA | Futur snapshot live et combo | Code prêt, validation réelle incomplète |
| Fixtures | Tests déterministes | Mécanique uniquement |

## Identité minimale d’une option

Une quote utile conserve :

- `conId` ;
- symbole local et trading class ;
- expiration, strike, call/put ;
- exchange et devise ;
- multiplicateur ;
- livrable et statut ajusté lorsque disponibles ;
- bid/ask et tailles ;
- volume et open interest ;
- IV et Greeks avec convention/provider ;
- type de donnée : live, frozen, delayed ou delayed-frozen ;
- timestamps provider/exchange/réception séparés.

## Trois niveaux de temps

1. `exchange` : horodatage produit par le marché ou une source officielle.
2. `provider` : horodatage produit par IBKR ou le fournisseur.
3. `client_received_at` : moment où notre processus reçoit le callback.

Le troisième niveau mesure la réception, pas l’âge réel de la quote. Le provider peut l’utiliser
pour conserver la donnée de recherche, mais `promotion_eligible` reste faux.

## Complétude

Le snapshot distingue :

- nombre de contrats découverts ;
- nombre de quotes utilisables ;
- nombre de quotes manquantes ou invalides ;
- fin complète de la découverte ;
- fin complète de la collecte ;
- éligibilité à la promotion.

Une chaîne avec 500 contrats découverts et 480 quotes valides n’est pas présentée comme complète.

## Hashes et lineage

Deux hashes sont séparés :

- `provider_metadata_hash` : identité et métadonnées contractuelles ;
- `raw_snapshot_hash` : contenu brut normalisé reçu du transport.

La conversion vers `MarketSnapshot` crée ensuite un `DatasetLineage`. Un hash prouve l’identité du
contenu observé, pas sa justesse économique ni ses droits d’utilisation.

## Valeurs absentes

Les valeurs manquantes restent `null`. Le moteur ne suppose pas :

- multiplicateur 100 sans preuve contractuelle ;
- dividende nul ;
- taux arbitraire ;
- commission nulle ;
- marge nulle ;
- slippage nul ;
- IV/Greek présent si le callback ne l’a pas fourni.

