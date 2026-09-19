# Diagnostic IBKR d’un ordre non rempli

Statut logiciel : `NO_FILL_DIAGNOSTICS = READY_OFFLINE`  
Validation sur ordre réel : `NOT_RUN`

## Règle fondamentale

`filled = 0` ne répond pas à « pourquoi ? ». Sans erreur, annulation ou preuve de marché suffisante,
la réponse correcte est `WORKING_NO_FILL_YET` ou `UNKNOWN_NO_FILL_REASON`, jamais « pas de
liquidité » ou « pas de contrepartie ».

## Arbre de diagnostic

```text
Ordre créé ?
├─ non → UNKNOWN
└─ oui
   ├─ transmit=false → LOCAL_NOT_TRANSMITTED
   ├─ précaution avant transmission → ORDER_PRECAUTION / revue humaine
   ├─ code de rejet → REJECTED + code + catégorie
   ├─ annulation prouvée → CANCELLED + cause prouvée ou UNKNOWN
   ├─ fill partiel → PARTIALLY_FILLED
   ├─ fill complet → FILLED
   ├─ Submitted, 0 fill, restant > 0 → WORKING_NO_FILL_YET
   └─ session/état incomplet → RECONCILIATION_REQUIRED
```

L’API `error` transporte aussi des avertissements ; elle n’est pas, à elle seule, la preuve d’un
rejet. Le booléen normalisé `order_rejected` et les autres callbacks déterminent la conclusion.
Référence officielle : [Error handling](https://interactivebrokers.github.io/tws-api/error_handling.html).

## Position de la limite dans le marché

Cette analyse n’est activable que si la convention de prix signé du BAG a été observée sur IBKR,
si le market data est live et si la cotation combo, toutes les jambes, le sous-jacent et, si
nécessaire, le FX sont frais.

Pour un **débit**, l’utilisateur autorise un débit maximal :

| Exemple bid/ask `5.10 / 5.40` | Diagnostic |
|---|---|
| limite `5.20` | `WORKING_INSIDE_SPREAD` |
| limite `5.25` | `WORKING_NEAR_ASK` |
| limite `5.40` | `IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE` |

Pour un **crédit**, l’utilisateur exige un crédit minimal. La direction économique est inverse :
une limite qui baisse accepte moins de crédit et devient plus agressive.

Même `IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE` ne garantit jamais un fill. Le carnet peut changer,
la taille visible peut être insuffisante, le routage peut prendre du temps et la cotation peut être
indicative.

## Résultats non conclusifs

| Situation | Résultat |
|---|---|
| convention BAG non vérifiée | `MARKETABILITY_UNKNOWN_PRICE_CONVENTION_UNVERIFIED` |
| cotation ou composant stale | `MARKETABILITY_UNKNOWN_DATA_STALE` |
| donnée delayed/frozen | `MARKETABILITY_UNKNOWN_DATA_NOT_LIVE` |
| bid/ask combo absent | `MARKETABILITY_UNKNOWN_NO_COMBO_QUOTE` |
| bid/ask incohérent | `MARKETABILITY_UNKNOWN_INVALID_QUOTE` |
| ordre retenu avec `whyHeld` | `BROKER_HELD` |
| session perdue | `STATE_UNKNOWN` / `RECONCILIATION_REQUIRED` |
| ordre valide dans le simulateur Paper sans fill | `PAPER_SIMULATOR_LIMITATION_POSSIBLE` ou `UNKNOWN_NO_FILL_REASON` |

Une annulation IOC/FOK n’est qualifiée `TIF_CONDITION_NOT_SATISFIED` que si l’évidence broker
soutient `TIF_EXPIRED`. Elle n’est pas transformée en diagnostic de liquidité.

Les fills Paper proviennent d’un simulateur top-of-book avec des limites propres, notamment sur
les combos et les options US au penny. Un non-fill Paper n’est donc jamais promu en preuve de
liquidité réelle. Voir [IBKR_PAPER_SIMULATOR_LIMITATIONS.md](IBKR_PAPER_SIMULATOR_LIMITATIONS.md).

## Snapshot figé à la soumission

Le diagnostic compare l’ordre à la réalité observée au moment concerné, pas au dernier prix connu
plus tard. Le snapshot immuable contient : ticker, candidat, stratégie, quantité, `conId`/ratio/action
de chaque jambe, type et fraîcheur de données, timestamp, bid/ask/mid combo, combo synthétique,
statut de convention signée, limite, débit/crédit, commission attendue, capital, perte maximale,
spread et âge de cotation.

Un second prix peut servir à constater `QUOTE_MOVED_AWAY`, mais ne remplace jamais le snapshot de
soumission.

## Ce que montre l’interface

La section **POSITION / EXECUTION → EXECUTION STATUS** expose :

- statut canonique et statut brut ;
- transmis ou non ;
- quantité remplie/restante et prix moyens ;
- âge de l’ordre et TIF ;
- limite et bid/ask/mid figés ;
- raison non-fill uniquement si elle est prouvée ;
- rejet/annulation et code broker ;
- timeline immuable ;
- éventuelle proposition de repricing, sans bouton d’envoi automatique.

Les ordres `WORKING` restent neutres/bleus, les fills verts, les partiels ambre, les rejets rouges,
les non-transmis ambre et les états ambigus orange. Le heatmap Research n’est pas modifié.

## Ancien test d’environ 50 €

La recherche dans le dépôt, les rapports et les traces documentées n’a trouvé aucun `orderStatus`,
`openOrder`, code d’erreur, log TWS/API, état `transmit`, avertissement ou preuve d’annulation
rattachable à ce test.

```text
historical_test = ~50 EUR demo test
root_cause = UNRESOLVED_NO_BROKER_EVIDENCE
```

`TRANSMIT_FALSE`, `API/TWS_PRECAUTION`, `MISSING_MARKET_DATA`, `PRICE_PRECAUTION` et
`INVALID/UNVERIFIED_ORDER_STATE` restent des hypothèses, sans classement ni préférence.

## Ce que « faible liquidité observée » demanderait

Une future qualification `LOW_OBSERVED_LIQUIDITY` devrait avoir une définition versionnée et des
preuves explicites : largeur du spread, tailles, volume et open interest. Le seul non-fill ne
suffira jamais. Cette qualification n’est pas implémentée ici.
