# Guide IBKR read-only — intégration future

Statut au 18 août 2026 : `configured_not_entitled_not_connected`

La V1 ne dépend pas d'IBKR. Le contrat de configuration locale est prêt, sans clé API,
mais aucun abonnement OPRA, identifiant de compte ou droit d'usage n'est affirmé et
aucune connexion n'a été tentée. Une intégration future doit rester un adaptateur de
données entrant, sans interface d'ordre.

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

## Allowlist proposée

- résolution du sous-jacent et des contrats ;
- découverte de chaîne via `reqSecDefOptParams` ;
- détails d'un contrat option déjà résolu ;
- snapshots de marché et historiques nécessaires aux IV/RV ;
- données de compte/marge en lecture seule lorsqu'elles sont explicitement autorisées.

IBKR indique que `reqContractDetails` sur un contrat incomplet peut retourner une chaîne mais peut
être ralenti par l'ambiguïté ; `reqSecDefOptParams` est la voie recommandée pour la découverte.
Chaque quote intégrée doit conserver `conId`, expiration, strike, right, trading class,
multiplicateur, exchange, devise et timestamp.

## Denylist absolue

`placeOrder`, modification, annulation, global cancel, transmission différée et construction de
ticket sont absents de l'adaptateur. `ReadOnlyBrokerGateway` lève `ForbiddenOperation` même si un
appelant tente submit/modify/cancel.

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
