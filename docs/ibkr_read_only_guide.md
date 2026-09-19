# Guide IBKR read-only — provider hors ligne, validation réelle future

Statut au 17 septembre 2026 : `READY_FOR_LIVE_READONLY_VALIDATION`

Le moteur offline ne dépend pas d'IBKR. L'adaptateur de données entrant est maintenant codé :
qualification, découverte de chaîne, snapshots, normalisation, cache/retry/pacing, BAG et
conversion vers le moteur. Il reste sans interface d'ordre. Aucun abonnement OPRA ni droit
d'usage n'est affirmé. Une preuve séparée a observé le handshake paper le 25 août ; la nouvelle
capture de chaîne n'a pas été exécutée sur IBKR.

## Paramétrage non secret

```text
OPRA_PROVIDER=ibkr_tws
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=17
IBKR_SESSION_MODE=paper
IBKR_MARKET_DATA_TYPE=delayed
OPRA_ENTITLEMENT_CONFIRMED=false
OPRA_LICENSE_REVIEWED=false
```

TWS/IB Gateway porte l'authentification de l'utilisateur. Le socket API utilise
`host`, `port` et `clientId`, et non une clé API IBKR. Ports paper par défaut : TWS
`7497`, IB Gateway `4002`. L'exemple est publié dans `.env.example` ; le fichier local
`.env` n'est pas modifié.

## Politique de connexion

1. Utiliser exclusivement un environnement paper dédié et un client ID réservé à la recherche.
2. Dans TWS, conserver **Read-Only API** activé. La documentation IBKR présente ce réglage dans
   `Global Configuration > API > Settings`; les instructions IBKR demandent de le désactiver pour
   un client capable d'ordonner, ce qui est précisément hors périmètre ici.
3. Appliquer une allowlist de requêtes de lecture et journaliser l'horodatage de chaque callback.
4. Ne jamais importer de module d'exécution dans `take_two_options.data`.
5. Rejouer les données reçues dans une fixture avant de les laisser alimenter un rapport.

## Allowlist implémentée

- résolution du sous-jacent et des contrats ;
- découverte de chaîne via `reqSecDefOptParams` ;
- détails d'un contrat option déjà résolu ;
- snapshots de marché et historiques nécessaires aux IV/RV ;
- données de compte/marge en lecture seule lorsqu'elles sont explicitement autorisées.

IBKR indique que `reqContractDetails` sur un contrat incomplet peut retourner une chaîne mais peut
être ralenti par l'ambiguïté ; `reqSecDefOptParams` est la voie recommandée pour la découverte.
Chaque quote intégrée doit conserver `conId`, expiration, strike, right, trading class,
multiplicateur, exchange, devise et timestamp.

## Provenance et fraîcheur

La provenance du timestamp et la preuve de fraîcheur sont deux faits distincts :

- `SOURCE_TIMESTAMP` exige un vrai timestamp exchange/provider, non futur et assez récent ;
- `BOUNDED_CAPTURE_WINDOW` accepte un snapshot live reçu dans la fenêtre bornée de la requête
  lorsque TWS ne fournit aucun timestamp source ;
- `UNVERIFIED` ne peut jamais être promu.

Un timestamp `client_received_at` reste étiqueté comme tel. Il n'est jamais copié dans
`exchange_timestamp` ou `provider_timestamp`. Une chaîne n'est promouvable que si le sous-jacent
et chaque jambe requise sont complets et classés `LIVE_SOURCE_TIMESTAMP_FRESH` ou
`LIVE_CAPTURE_WINDOW_FRESH`. Les données delayed, frozen, invalides, incomplètes ou périmées
restent visibles pour diagnostic mais ne sont pas promouvables. Une BAG est évaluée séparément :
sa propre fraîcheur ne peut pas être déduite de celle des jambes.

## Denylist absolue

`placeOrder`, modification, annulation, global cancel, transmission différée et construction de
ticket sont absents de l'adaptateur de marché. Le bridge d'exécution séparé conserve son
`DisabledGateway` et ses propres blocages ; il n'est pas activé par le provider de chaîne.

## Statut opérationnel exact

- `IBKR_PROVIDER_IMPLEMENTATION = READY_FOR_LIVE_READONLY_VALIDATION`
- `IBKR_LIVE_DATA_VALIDATION = NOT_RUN`
- `OPRA_ENTITLEMENT = UNCONFIRMED`
- `SHADOW_CAMPAIGN = NOT_STARTED`
- `PAPER_EXECUTION = DISABLED`
- `LIVE_EXECUTION = FORBIDDEN`
- `HOLDOUT = UNOPENED`

## Sources officielles vérifiées le 2026-08-18

- [IBKR TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR contract documentation](https://ibkrcampus.com/campus/ibkr-api-page/contracts/)
- [IBKR TWS API reference](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-ref/)
- [IBKR market data permissions](https://ibkrcampus.com/campus/trading-lessons/trade-permissions-mkt/)
- [IBKR market data subscriptions](https://ibkrcampus.com/docs/general/market-data-subscriptions/introduction)
- [OPRA fee schedule](https://cdn.opraplan.com/documents/OPRA_Fee_Schedule.pdf)
- [OPRA subscriber agreement](https://cdn.opraplan.com/documents/OPRA_Exhibit_A.pdf)
- [OCC options disclosure document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document)

Ces liens sont des sources externes courantes, pas des validations de stratégie. Version API,
permissions, abonnements de marché, frais et règles de marge doivent être reverifiés au moment de
l'intégration.
