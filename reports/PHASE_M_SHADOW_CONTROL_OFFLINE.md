# Phase M — contrôle de campagne shadow hors ligne

Date : 17 septembre 2026  
Statut : `CONTROL_PLANE_TESTED_CAMPAIGN_NOT_STARTED`

## Implémentation

- manifeste strict `ShadowCampaignManifest` avec période, seuils, hashes et approbations ;
- aucun seuil logiciel par défaut : les valeurs restent une décision du responsable risque ;
- journal de décisions append-only, numéroté et hash-chaîné ;
- journal de réalisations séparé, lui aussi numéroté et hash-chaîné ;
- lien obligatoire de chaque réalisation vers l'identifiant et le hash exact de sa décision ;
- contrôles de chronologie, unicité, fenêtre, commit et configuration ;
- commande provider-free `ttwo-options paper shadow-status` ;
- statuts distincts pour brouillon bloqué, prêt, en cours, cible atteinte en attente de revue,
  fenêtre incomplète et échec sûr ;
- invariants constants `paper_validation_passed=false`, `promotion_eligible=false`,
  `transmit=false`, `order_capability=forbidden`.

## Frontière de preuve

Les contrats et transitions sont testés avec des observations synthétiques identifiées. Aucune
campagne shadow ou paper n'a été démarrée, aucune décision prospective réelle n'a été enregistrée
et aucun seuil n'a été approuvé. Le manifeste commité est `draft_to_validate` et
`example_only=true`.

L'atteinte future des cibles de comptage permettra seulement d'affirmer que des observations ont
été enregistrées. La qualité, les incidents, les coûts, le slippage et l'acceptation de la campagne
resteront soumis à une revue humaine documentée.

## Validation locale

- 428 tests Python ;
- Ruff et mypy strict sur 199 fichiers source ;
- 40 schémas JSON à jour ;
- artefacts offline, registre, audits Phase 10/11, sécurité et dépendances valides ;
- 14 tests bridge et 64 tests Worker ;
- scan de 177 fichiers Python : aucun import d'ordre interdit, aucun `transmit=true`.

Aucun appel IBKR, Oracle ou Cloudflare distant n'a été requis pour tester cette couche.
