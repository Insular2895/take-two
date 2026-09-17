# Éléments ouverts et preuves attendues

## Bloquants humains

| Élément | Pourquoi le code ne peut pas décider | Preuve attendue |
|---|---|---|
| Entitlement OPRA | Dépend du compte et de l’abonnement | Vérification titulaire/IBKR |
| Licence et stockage | Dépend des accords applicables | Validation documentée |
| Usage commercial | Dépend du produit et de la redistribution | Avis contractuel/juridique |
| Seuils paper | Décision de risque | Validation explicite du responsable risque |
| Ouverture holdout | Décision irréversible | Gate historique/walk-forward puis autorisation |

## Validation live read-only

Le protocole, le rapport JSON/Markdown, la seconde session indépendante et la BAG optionnelle sont
`TESTÉ_OFFLINE`. Les cases restent ouvertes tant que le broker réel n'a pas fourni les preuves.

- [ ] nouvelle commande testée avec `ibapi` officiel ;
- [ ] qualification TTWO unique ;
- [ ] chaîne réelle non vide ;
- [ ] `conId`, expirations, strikes, multiplier et trading class contrôlés ;
- [ ] volume, OI et Greeks contrôlés selon abonnement ;
- [ ] type live/delayed contrôlé ;
- [ ] timestamps réels compris ;
- [ ] reconnexion testée ;
- [ ] pacing observé ;
- [ ] quote BAG et convention signée validées ;
- [ ] écart BAG/synthétique mesuré.

## Télémétrie Cloudflare

- [ ] position TTWO paper de test présente ;
- [ ] payload redacted réel publié ;
- [ ] signature, Access et anti-rejeu vérifiés ;
- [ ] D1 et dashboard montrent la même observation ;
- [ ] perte de connexion devient stale/degraded ;
- [ ] aucun identifiant de compte dans logs ou payload.

Compatibilité locale supplémentaire : le même vecteur HMAC est accepté côté Python et Worker.
Cela ne coche pas le trajet distant complet.

## What-if et paper

Non implémenté dans la frontière ordre :

- demande IBKR what-if ;
- commission et marge broker ;
- callbacks d’ordres/fills ;
- partial fills/rejets/annulations ;
- recovery `orderRef`/`permId`/`execId` ;
- protection native ;
- exécution paper.

Ces éléments nécessitent une décision distincte parce qu’ils élargissent la frontière vers le
domaine ordre, même en paper.

Le **contrôle offline** de campagne shadow est maintenant codé : manifeste à approbation humaine,
journaux décision/réalisation hash-chaînés et rapport d'état. La campagne réelle reste non
commencée et les seuils restent `draft_to_validate`. Il faut encore :

- [ ] valider la période et les tailles minimales avec le responsable risque ;
- [ ] geler les hashes IBKR, holdout, configuration et commit ;
- [ ] approuver les droits d'usage des données ;
- [ ] brancher la production prospective des décisions, sans backfill ;
- [ ] collecter les réalisations futures et les incidents ;
- [ ] effectuer une revue humaine finale, sans promotion automatique.

## Dette documentaire/technique

- [x] aligner les pages d'état actives avec le handshake déjà observé ; les rapports historiques
  restent volontairement inchangés ;
- [ ] intégrer la branche IBKR dans `main` après revue ;
- [ ] aligner la version package et le changelog lors de la release ;
- [x] figer et pousser le premier commit de handoff (`0eca2f3`) avec ses résultats de tests ;
- [x] mettre à jour le vault pour le checkpoint provider du 16 septembre ;
- [ ] figer et pousser le checkpoint protocole de validation du 17 septembre.
