# Phase M — protocole de validation IBKR hors ligne

Date : 17 septembre 2026

Statut : `OFFLINE_PROTOCOL_COMPLETE_LIVE_RUN_PENDING`

## Implémentation

- commande unique `ttwo-options data ibkr-validate --connect-read-only` ;
- deux contrôles health indépendants ;
- rapport strict des identités, complétude, volume, OI, Greeks, timestamps et type de marché ;
- plan BAG humain par expiration/strike/type, résolu vers les `conId` de la chaîne ;
- statuts distincts pour échec sûr, capture non promouvable et promotion data stricte ;
- JSON/Markdown redacted, chaîne et snapshot moteur sous `reports/private/` ignoré par Git ;
- schémas `ComboValidationPlan` et `IbkrReadOnlyValidationReport` ;
- vecteur HMAC commun prouvant la compatibilité locale Python/Cloudflare.

## Frontière de preuve

Le protocole est testé avec provider injecté et signatures locales. Aucun appel IBKR, Oracle ou
Cloudflare distant n'a été effectué. La seconde session ne remplace pas encore une coupure réseau
pendant une collecte. `CHAIN_*_PROMOTION_ELIGIBLE` ne concerne que l'artefact data et ne vaut ni
validation de stratégie, ni autorisation paper, ni entitlement/licence.

## Validation locale

- 428 tests Python ;
- Ruff et mypy strict sur 199 fichiers source ;
- 40 schémas JSON, artefacts offline, registre, sécurité et dépendances ;
- scan de 177 fichiers Python : aucun import d'ordre interdit, aucun `transmit=true` ;
- 14 tests et Ruff pour le bridge ;
- 64 tests, typecheck et safety scan pour le Worker.

L'exécution reste absente et `order_capability=forbidden`.
