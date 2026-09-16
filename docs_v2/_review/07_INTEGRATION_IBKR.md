# Intégration IBKR read-only

## Authentification réelle

La TWS API n’utilise pas une clé API classique. L’utilisateur se connecte dans TWS ou IB Gateway,
puis le client local ouvre un socket avec `host`, `port` et `clientId`.

Ports paper usuels du projet :

- TWS : `7497` ;
- IB Gateway : `4002`.

Le provider officiel refuse un hôte non loopback et une session configurée `live`.

## Séquence de capture d’une chaîne

```text
1. handshake + managedAccounts
2. vérifier un unique compte paper DU
3. qualifier TTWO STK via reqContractDetails
4. snapshot du sous-jacent
5. reqSecDefOptParams pour les expirations/trading classes
6. reqContractDetails par expiration/trading class
7. borner expirations/trading classes, filtrer dates/strikes et dédupliquer les conId
8. refuser si maximum_contracts est dépassé
9. snapshots options en lots bornés
10. collecter bid/ask, tailles, volume, OI, IV et Greeks
11. normaliser, hasher et convertir vers MarketSnapshot
12. déconnexion propre
```

## Retry, pacing et cache

- retry : seulement `IbkrTransientError`, nombre borné ;
- pacing provider : intervalle minimal entre opérations ;
- pacing transport : espacement entre appels et lots de taille bornée ;
- cache : mémoire seulement, TTL court ;
- panne après expiration : erreur, jamais ancien snapshot silencieux.

Ces politiques sont testées offline. Les vraies limites de l’abonnement et le comportement de la
session devront être observés puis ajustés sans dépasser les règles IBKR.

## Quote BAG

Le transport construit un `Contract` de type `BAG` avec des `ComboLeg` qualifiées, puis demande une
quote de marché snapshot. Il ne construit aucun `Order`.

Le synthétique suit une convention net-debit signée :

```text
ask synthétique = somme(BUY ask) - somme(SELL bid)
bid synthétique = somme(BUY bid) - somme(SELL ask)
```

Une valeur négative représente un crédit. La comparaison BAG/synthétique n’est confirmée que si :

- les deux côtés BAG sont présents et frais ;
- les jambes ont bid/ask ;
- la convention signée IBKR a été vérifiée en session réelle.

Les prix BAG observés restent visibles quand le timestamp ou la convention ne sont pas encore
confirmés, mais `comparison_confirmed` reste faux. Observation et validation ne sont pas
confondues.

## What-if, commissions et marge

Le modèle `BrokerWhatIfEvidence` est codé pour ingérer une observation future sans inventer les
champs manquants. Le provider ne demande pas lui-même le what-if, car cette voie peut nécessiter un
objet et une méthode du domaine ordre. Cette capacité reste hors de la frontière read-only.

## Preuve réelle déjà disponible

Le 25 août 2026, le projet a réussi un handshake paper sur Oracle, vérifié le compte `DU` et
produit un snapshot redacted sans position TTWO. Cette preuve couvre la connexion de base. Elle ne
couvre pas la nouvelle implémentation de chaîne, BAG, OI, Greeks ou pacing.
