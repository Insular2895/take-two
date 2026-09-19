# Sécurité et frontière d’exécution

## Invariants

- aucune soumission, modification, annulation ou exercice dans le runtime par défaut ;
- moteur/provider/télémétrie : `order_capability=forbidden` ; adaptateur Paper isolé :
  `READY_OFFLINE_DISARMED`, confirmation humaine obligatoire et Live absent ;
- connecteurs live désactivés par défaut et injectés comme ports read-only ;
- aucune clé dans le dépôt, les rapports, l’HTML ou les logs ;
- erreur réseau fail-closed et données manquantes jamais remplacées ;
- HTML V11 autonome, sans requête réseau ni calcul financier côté client ;
- fixtures toujours marquées `synthetic` et non promouvables.

Ces invariants continuent de s'appliquer au moteur de recherche. La fondation IBKR paper approuvée
le 25 août 2026 est isolée sous `services/ibkr-paper-bridge`; elle démarre désactivée, refuse le mode
live, exige un compte `DU`, n'expose aucun port broker, journalise avant dispatch et transforme un
timeout ambigu en réconciliation obligatoire plutôt qu'en nouvel envoi.

Le test `assert_all_execution_paths_forbidden()` inspecte tous les fichiers Python du package
pour les imports, définitions et appels d’ordre interdits ainsi que `transmit=True`. Le script
`scripts/security_gate.py` sépare et rapporte cinq frontières : moteur de recherche interdit
d'ordre, provider marché read-only interdit d'ordre, télémétrie read-only interdite d'ordre,
adaptateur paper désactivé et exécution live interdite. Un contrôle AST distinct prouve que le
runtime du bridge construit toujours `DisabledGateway`; le protocole `PaperGateway` peut conserver
son interface sans constituer une capacité active.

La préparation finale ajoutée le 19 septembre 2026 ne change pas le runtime par défaut. Les
fermetures refusent toujours `transmit=true`. Une entrée confirmée peut contenir ce drapeau dans
son contrat immuable, mais reste `dispatch_authorized=0` dans D1 et `main.py` construit toujours
`DisabledGateway`. Les normaliseurs de callbacks,
le diagnostic de marketability et le repricing borné sont des fonctions pures sans primitive de
soumission, modification ou annulation. Les preuves affichables excluent le payload brut et
l’advanced rejection JSON ; compte, mot de passe, token, secret et clé API sont nettoyés avant la
persistance structurée.

L'audit runtime Cloudflare est un gate CI : `npm audit --omit=dev --audit-level=high`. Les quatre
alertes high initiales du 17 septembre 2026 concernaient uniquement la chaîne dev/test
Wrangler → Miniflare → Sharp. Les mises à niveau mineures compatibles vers Wrangler `4.134.0`,
plugin Vitest `1.1.12`, types Workers `5.20260917.1` et Sharp transitif `0.35.4` ramènent les audits
complet et runtime à zéro vulnérabilité. Ces outils ne figurent pas dans le bundle Worker dry-run.

## Exécution locale

```bash
python scripts/security_gate.py
pytest -q
```

Les fichiers `.env*` sont ignorés par Git, sauf exemple sans secret. Le scanner vérifie
les fichiers suivis sans afficher le contenu d’un environnement local.

## État de préparation au 17 septembre 2026

- frontière d'exécution et scan offline : `COMPLETE_SOFTWARE_CONTROLS` ;
- IBKR : handshake paper et compte `DU` observés le 25 août dans le bridge Oracle ; le provider
  de chaîne ajouté en septembre est testé hors ligne, désarmé sans `--connect-read-only` et bloqué
  avant I/O tant que l'entitlement et la licence ne sont pas confirmés ;
- transport de chaîne : loopback, paper et compte `DU` obligatoires ; aucune importation de type
  d'ordre, aucun submit/modify/cancel/exercise ;
- `PAPER_ADAPTER_CODE=READY_OFFLINE`, mais `PAPER_RUNTIME_DEFAULT=DISABLED`,
  `PAPER_REAL_ORDER_TEST=NOT_RUN`, entitlement OPRA non confirmé et campagne shadow non commencée ;
- audit de frontière :
  [`audits/PRE_ENTITLEMENT_BOUNDARY_2026-08-18.md`](audits/PRE_ENTITLEMENT_BOUNDARY_2026-08-18.md) ;
- revue indépendante, threat model, SAST/dépendances, pentest et réponse à incident :
  `REQUIRED_BEFORE_COMMERCIAL_GATE`.

## Limites

Ce contrôle statique ne remplace pas une revue indépendante, un threat model, du SAST,
une analyse de dépendances, une rotation de secrets ou un test d’intrusion. Ces preuves
sont exigées avant le gate commercial.
