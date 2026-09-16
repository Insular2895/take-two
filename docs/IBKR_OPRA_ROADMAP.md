# Roadmap IBKR / OPRA read-only

## Phase 1 — Entitlements

Configurer d'abord le socket local sans secret : `OPRA_PROVIDER=ibkr_tws`, hôte,
port, client ID, mode `paper` et type de données. IBKR TWS/IB Gateway ne demande pas
de clé API. Conserver `OPRA_ENTITLEMENT_CONFIRMED=false` et
`OPRA_LICENSE_REVIEWED=false` jusqu'à vérification humaine.

Vérifier le compte IBKR, les permissions options, l’abonnement OPRA applicable, les
accords de redistribution, les coûts et les limites snapshots/temps réel. Archiver
l’approbation juridique et data.

## Phase 2 — Market data seulement

Injecter une session TWS ou IB Gateway dans le port existant. Tester qualification des
contrats, chaîne, spot, bid/ask, OI, volume, model Greeks, timestamps, reconnexion,
rate limits et comportement fail-closed.

## Phase 3 — Surface

Nettoyer les quotes, vérifier arbitrages, interpoler, calibrer local vol/Heston et
archiver l’erreur de calibration. Interdire un fallback pour toute décision promue.

## Phase 4 — Combos

Qualifier chaque jambe, construire le BAG, récupérer la quote combo, la comparer au
synthétique, définir un seuil de divergence et bloquer si la combo n’est pas confirmée.

## Phase 5 — Preview

Ajouter commissions estimées et marge what-if si disponible. Le ticket reste limité,
expirant, journalisé et soumis à confirmation humaine avec :

```text
transmit=false
what_if=true
human_confirmation_required=true
order_capability=forbidden
```

## Phase 6 — Paper

Mesurer remplissages, slippage, partial fills, rejets et annulations dans un compte
paper. La durée minimale reste à valider dans
[PAPER_TRADING_PLAN.md](PAPER_TRADING_PLAN.md).

## Checkpoint code au 16 septembre 2026

- phases 2 et 4 : implémentées et testées hors ligne, pas encore observées sur une chaîne réelle ;
- phase 1 : paramètres présents, mais entitlement et licence toujours non confirmés humainement ;
- phase 3 : briques quantitatives présentes, validation sur chaîne autorisée manquante ;
- phase 5 : contrat d'ingestion what-if présent, requête broker volontairement absente de cette
  frontière read-only ;
- phase 6 : non commencée.

Le transport officiel peut ouvrir une session uniquement après le drapeau CLI explicite
`--connect-read-only`. Il impose loopback, mode paper, compte `DU`, allowlist TTWO et n'importe
aucun type d'ordre. Aucune connexion n'a été effectuée pour ce checkpoint. Une preuve antérieure
du 25 août couvre seulement le handshake paper et la télémétrie de position, pas le nouveau
provider de chaîne. Aucune transmission d'ordre n'est mise en œuvre.
