# Guide IBKR read-only — intégration future

Statut : `design_only_not_connected`

La V1 ne dépend pas d'IBKR et ne demande aucun identifiant. Une intégration future doit rester un
adaptateur de données entrant, sans interface d'ordre.

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

## Sources officielles vérifiées le 2026-07-18

- [IBKR TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR contract documentation](https://ibkrcampus.com/campus/ibkr-api-page/contracts/)
- [IBKR TWS API reference](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-ref/)
- [OCC options disclosure document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document)

Ces liens sont des sources externes courantes, pas des validations de stratégie. Version API,
permissions, abonnements de marché, frais et règles de marge doivent être reverifiés au moment de
l'intégration.
