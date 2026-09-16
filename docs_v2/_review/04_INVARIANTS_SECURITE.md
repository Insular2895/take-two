# Invariants de sécurité

## Invariants permanents du moteur

```text
read_only = true
transmit = false
what_if = true
order_capability = forbidden
human_confirmation_required = true
```

`what_if=true` décrit le ticket et le statut attendu d’une preuve future. Cela ne signifie pas que
le moteur possède une méthode d’ordre what-if.

## Ce que le code refuse

- session IBKR live ;
- hôte IBKR non loopback ;
- compte non paper dans le bridge de télémétrie ;
- ticker hors allowlist ;
- entitlement ou licence non confirmés ;
- expiration ou strike hors requête ;
- contrat sans `conId`, multiplicateur ou identité valide ;
- bid/ask croisé, négatif ou non fini ;
- timestamp naïf ou venant du futur ;
- chaîne dépassant la borne déclarée ;
- doublon de `conId` ;
- fallback stale après expiration du cache ;
- promotion d’une donnée delayed ou horodatée seulement à la réception ;
- quote BAG « confirmée » sans convention de prix validée ;
- inconnue de marge ou commission transformée en zéro.

## Séparation des credentials

| Credential | Usage | Ne doit jamais permettre |
|---|---|---|
| Session IB Gateway | Authentification broker locale | Exposition publique du socket |
| HMAC télémétrie | Publication du snapshot read-only | Claim ou événement d’exécution |
| HMAC bridge paper | Contrôle futur isolé | Mode live ou compte non `DU` |
| Cloudflare Access service token | Passage de la politique Access | Validation HMAC à lui seul |
| Mot de passe d’action humain | Mutations sensibles du registre | Authentification broker |

## Frontière statique

Le scan recherche les imports d’ordre, les méthodes `placeOrder`, `cancelOrder`, exercice et les
littéraux `transmit=true`. Le transport officiel importe `ibapi.client`, `ibapi.wrapper` et les
types de contrat/BAG, mais jamais `ibapi.order`.

## Limite honnête

Un scan statique n’est pas une preuve absolue. Avant tout produit commercial, il faut encore une
revue indépendante, analyse de dépendances, threat model, rotation testée, sauvegarde/restauration,
pentest et procédure d’incident.

