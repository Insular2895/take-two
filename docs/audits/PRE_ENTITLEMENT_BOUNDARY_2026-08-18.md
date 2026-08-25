# Audit de frontière pré-entitlement — 18 août 2026

Décision utilisateur : terminer les améliorations reproductibles, puis s'arrêter avant
toute connexion IBKR/OPRA payante. Cette décision autorise la publication de la CI et
des contrats de configuration ; elle n'autorise ni achat, ni connexion, ni ouverture du
holdout, ni campagne paper fictive.

## Résultat immédiat

| Domaine | Fait vérifié | Statut | Prochaine preuve exigée |
| --- | --- | --- | --- |
| CI offline | Workflow publié, contrôles offline verts sur la branche | `COMPLETE_OFFLINE` | Maintenir la branche verte après ce changement |
| Historique | Données privées réelles et point-in-time utilisées ; droits du compte encore à confirmer | `DIAGNOSTIC_CONDITIONAL_RIGHTS` | Confirmation écrite du titulaire et nouvel échantillon futur |
| Calibration | Empirique, EWMA, GARCH/GJR et surfaces diagnostiqués ; Heston bloqué | `DIAGNOSTIC_NOT_PROMOTED` | Échantillon suffisant, stabilité OOS et seuils validés |
| Walk-forward | 25 observations alignées, 10 résultats OOS, minimum formel 41 | `INSUFFICIENT_SAMPLE` | Accumuler des observations sans retuning opportuniste |
| Holdout final | Ledger initialisé, contenu jamais ouvert | `UNOPENED` | Ouverture unique selon protocole, seulement après les gates antérieurs |
| IBKR/OPRA | Socket TWS paper paramétré sans clé API ; licence et entitlement à `false` | `CONFIGURED_NOT_ENTITLED` | Titulaire du compte, abonnement, accords, session paper read-only |
| Quotes/coûts/marge | Contrats et gates définis ; aucune observation broker | `NOT_VALIDATED` | Combo réel, commissions et marge what-if disponibles, sinon blocage |
| Campagne paper | Plan et ledgers prêts, aucune décision prospective enregistrée | `BLOCKED_BEFORE_START` | Gates historique/walk-forward et flux autorisé |
| Sécurité | Frontière d'ordre interdite, scan secrets/capacités et tests offline | `SOFTWARE_CONTROLS_COMPLETE` | Revue indépendante, SAST/dépendances, threat model et pentest avant commercial |
| Juridique/data | Restrictions et sources officielles documentées | `HUMAN_COUNSEL_REQUIRED` | Qualification compte/usage/juridiction et avis professionnel |
| Commercial | Plan et prompt de reprise archivés ; gate Phase N fermé | `DORMANT_FORBIDDEN` | Phase M, shadow, paper, validation finale et GO explicite |

## Faits, inférences et décisions

- Fait : IBKR TWS/IB Gateway expose un socket local après authentification dans
  l'application ; cette voie ne demande pas de clé API IBKR.
- Fait : les abonnements et permissions de marché sont liés au compte/utilisateur et ne
  peuvent pas être déduits du dépôt.
- Inférence : avec 10 résultats OOS, relancer une sélection ou ouvrir le holdout
  augmenterait le risque d'overfit sans satisfaire la politique formelle.
- Décision actuelle : préserver `NO_POSITION_RECOMMENDED`,
  `ENGINE_NOT_PROVEN_SUPERIOR`, `transmit=false`, `what_if=true` et
  `order_capability=forbidden`.
- Décision encore requise : achat/activation des données, durée et seuils paper,
  ouverture du holdout, toute évolution produit ou commerciale.

## Point d'arrêt reproductible

L'exemple non secret est dans `.env.example`. La commande ci-dessous valide la forme de
la configuration et reconstruit les rapports sans ouvrir de session :

```bash
ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml
```

Résultat attendu avant abonnement : `CONFIGURED_NOT_ENTITLED`,
`connection_attempted=false`, `phase_m_started=false`. Toute preuve de quote combo,
coût, marge ou résultat paper reste interdite tant qu'elle n'a pas été réellement
observée et archivée.

## Prompt commercial conservé

Le prompt demandé pour une reprise future se trouve dans
`docs/commercial/COMMERCIALIZATION_RESUME_PROMPT.md`. Son statut reste
`DORMANT_PROMPT_NOT_EXECUTABLE_TODAY`.

## Sources officielles

- [IBKR TWS API](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR market data permissions](https://ibkrcampus.com/campus/trading-lessons/trade-permissions-mkt/)
- [IBKR market data subscriptions](https://ibkrcampus.com/docs/general/market-data-subscriptions/introduction)
- [OPRA fee schedule](https://cdn.opraplan.com/documents/OPRA_Fee_Schedule.pdf)
- [OPRA subscriber agreement](https://cdn.opraplan.com/documents/OPRA_Exhibit_A.pdf)

Ces sources ne constituent ni conseil juridique ni confirmation des droits du compte.
