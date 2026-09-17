# Phase M — clôture du code offline avant connexion

Date : 17 septembre 2026  
Statut maximal : `OFFLINE_CONTROL_READY_NOT_LIVE_VALIDATED`

## Résultat

Le dépôt contient maintenant les mécanismes sûrs réalisables sans brancher IBKR :

- provider options TTWO paper/loopback/read-only, qualification, chaîne, spot, volume, OI, Greeks ;
- quotes BAG et comparaison synthétique ;
- retry, pacing, cache court et diagnostics sans stale fallback ;
- protocole de validation réel explicitement armé et rapports redacted ;
- normalisation offline des commissions/marges what-if déjà observées ;
- consommation typée de cette preuve par les previews ;
- journaux shadow décision/réalisation append-only, hash-chaînés et liés à une campagne ;
- commandes d'append soumises à manifeste approuvé, commit/config figés, fenêtre et délais ;
- télémétrie Cloudflare signée testée localement jusqu'à l'ingestion D1/API authentifiée.

## Frontière conservée

Le transport de marché n'importe ni classe d'ordre, ni `placeOrder`, ni annulation, ni exercice.
`transmit=false` et `order_capability=forbidden` restent invariants. Le mécanisme IBKR qui produit
un what-if est ordre-shaped ; seul son résultat redacted peut entrer dans ce dépôt aujourd'hui.

## Preuves offline exécutées

- 439 tests Python passés ;
- 14 tests du bridge Oracle passés ;
- 64 tests Worker Cloudflare dans 8 fichiers passés ;
- Ruff passé ; mypy passé sur 200 fichiers source ;
- 44 schémas JSON déterministes exportés et vérifiés ;
- validateurs d'artefacts et registre recherche passés ;
- security gate passé sur 178 fichiers Python : 0 import ordre, 0 `transmit=true` ;
- tests dédiés aux sentinelles/devises/inconnues what-if, au retry/cache sans stale fallback,
  aux délais shadow, aux chaînes de hash et aux exemples bloqués.

Seul avertissement observé : dépendance `websockets.legacy` dépréciée dans l'environnement de test.
Il ne provoque aucun échec mais doit être traité lors d'une future maintenance de dépendances.

## Ce que ce rapport ne valide pas

- entitlement OPRA, licence, stockage ou redistribution ;
- comportement réel des callbacks et limites IBKR ;
- valeurs de commission/marge what-if ;
- trajet Oracle/Cloudflare distant complet ;
- campagne shadow/paper ou performance prospective ;
- exécution, fills, rejets, annulations ou reprise d'ordres.

## Prochain gate humain

Valider les droits OPRA/licence, préparer IB Gateway Paper en read-only, puis lancer uniquement
`ttwo-options data ibkr-validate --connect-read-only ...`. Archiver le JSON, le Markdown et les
logs redacted. Aucune étape shadow ou paper ne doit démarrer automatiquement après ce run.
