# Décisions et compromis

Ce registre explique les choix actuels. Un changement de décision doit nommer les invariants,
tests, documents et risques touchés.

| ID | Choix | Pourquoi | Conséquence |
|---|---|---|---|
| TT-D01 | Python pour le moteur de recherche | Écosystème quantitatif et vitesse d’itération | Pas de promesse de faible latence |
| TT-D02 | Un pipeline décisionnel canonique | Évite deux vérités économiques | Les chemins legacy ne pilotent plus les verdicts |
| TT-D03 | QuantLib comme contrôle autoritatif | Gère les options américaines et les dividendes | Le fast path doit prouver sa parité ou retomber sur QuantLib |
| TT-D04 | Séparer mesures `P` et `Q` | Un prix risque-neutre n’est pas une probabilité réelle | Seuls les modèles `P/DECISION_ELIGIBLE` pilotent EV et probabilités |
| TT-D05 | Hard gates avant Pareto et score | Un bon score ne répare pas une donnée invalide | Les inconnus bloquants restent bloquants |
| TT-D06 | IBKR read-only injecté | Tester sans broker et isoler les callbacks | Aucun type IBKR dans le cœur quantitatif |
| TT-D07 | Package officiel IBKR installé localement | Évite un package tiers non maîtrisé | Import dynamique ; le dépôt ne vendore pas `ibapi` |
| TT-D08 | Paper uniquement, loopback et compte `DU` | Réduit le risque d’une erreur de configuration | Toute session live est refusée par le provider |
| TT-D09 | Gates entitlement/licence avant I/O | Le code ne peut pas déduire les droits du compte | Les deux validations humaines doivent être vraies |
| TT-D10 | Chaîne bornée par requête | Une chaîne illimitée crée pacing, mémoire et délais non maîtrisés | Dépassement = erreur, jamais troncature silencieuse |
| TT-D11 | Cache mémoire court, aucun stale fallback | Évite la persistance involontaire et les décisions sur données anciennes | Une panne après expiration bloque la lecture |
| TT-D12 | Retry uniquement pour les lectures | Une lecture peut être répétée sans double ordre | Aucun retry d’exécution n’existe ici |
| TT-D13 | Heure de réception distincte de l’heure provider | Ne pas fabriquer un timestamp marché | Un timestamp client empêche la promotion |
| TT-D14 | BAG demandé comme donnée de marché | Comparer combo réel et synthétique sans ordre | La convention signée doit être validée en session réelle |
| TT-D15 | What-if = contrat d’ingestion seulement | IBKR peut utiliser une voie assimilée à une soumission d’ordre what-if | Aucun appel what-if n’est ajouté au moteur read-only |
| TT-D16 | `NO_TRADE` reste une vraie alternative | Le budget ne doit pas forcer une position | L’allocation peut conserver 100 % de cash |
| TT-D17 | Holdout final non ouvert | Empêcher le retuning sur le dernier test | Le manque de données ne peut pas être fabriqué |
| TT-D18 | Oracle pour la session persistante | Le Mac ne doit pas être nécessaire en continu | Il faut sécuriser SSH, 2FA et reprise de la VM |

## Compromis principaux

### Chaîne « complète » contre sécurité opérationnelle

« Complète » signifie ici : tous les contrats qualifiés dans l’intervalle d’expirations et de
strikes demandé. Le provider refuse si ce périmètre dépasse `maximum_contracts`. Demander toutes
les expirations et tous les strikes sans borne n’est pas une preuve de qualité ; c’est un risque de
pacing et de timeout.

### Snapshot contre streaming

La première version utilise des snapshots bornés. Cela simplifie le cut-off, les hashes et la
reproductibilité. Un streaming futur devra prouver sa cohérence, ses séquences, sa reconnexion et
son snapshot atomique avant de remplacer ce chemin.

### What-if contre frontière d’ordre

Une estimation IBKR de commission/marge peut nécessiter des objets et appels du domaine ordre,
même avec `whatIf=true`. La décision actuelle est de ne pas introduire cette capacité dans le
moteur. Le moteur sait ingérer une preuve future, mais ne la demande pas lui-même.

