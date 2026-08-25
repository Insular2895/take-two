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

Ce dépôt s'arrête actuellement à la configuration locale non connectée. Il ne met en
œuvre ni activation de session, ni validation d'entitlement, ni transmission d’ordre.
