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

## What-if et paper

Non implémenté par le provider read-only :

- demande IBKR what-if ;
- commission et marge broker ;
- callbacks d’ordres/fills ;
- partial fills/rejets/annulations ;
- recovery `orderRef`/`permId`/`execId` ;
- protection native ;
- campagne shadow/paper.

Ces éléments nécessitent une décision distincte parce qu’ils élargissent la frontière vers le
domaine ordre, même en paper.

## Dette documentaire/technique

- [x] aligner les pages d'état actives avec le handshake déjà observé ; les rapports historiques
  restent volontairement inchangés ;
- [ ] intégrer la branche IBKR dans `main` après revue ;
- [ ] aligner la version package et le changelog lors de la release ;
- [ ] figer un commit de handoff et enregistrer ses résultats de tests ;
- [ ] mettre à jour le vault après validation de ce checkpoint.
