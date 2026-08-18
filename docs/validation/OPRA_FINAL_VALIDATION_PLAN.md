# Phase M future — plan de validation finale OPRA

Statut actuel au 18 août 2026 : `CONFIGURED_NOT_ENTITLED`. La Phase M n'est pas
démarrée. Ce plan n'autorise ni connexion aujourd'hui, ni ordre réel, ni création
d'un faux holdout.

## Configuration IBKR retenue jusqu'au point d'arrêt

```text
OPRA_PROVIDER=ibkr_tws
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=17
IBKR_SESSION_MODE=paper
IBKR_MARKET_DATA_TYPE=delayed
OPRA_ENTITLEMENT_CONFIRMED=false
OPRA_LICENSE_REVIEWED=false
```

IBKR TWS/IB Gateway n'utilise pas de clé API OPRA : l'utilisateur s'authentifie dans
l'application locale, puis le client se connecte au socket avec `host`, `port` et
`clientId`. `7497` est le port paper TWS par défaut ; `4002` est le port paper IB
Gateway par défaut. Les valeurs doivent être vérifiées dans
`Global Configuration > API > Settings`. Pour ce port de recherche, **Read-Only API
reste activé**.

Les deux confirmations restent volontairement à `false` tant que le titulaire du
compte n'a pas vérifié l'abonnement de marché, les accords OPRA, le stockage et
l'usage prévu. Un futur fournisseur à jeton utiliserait séparément
`OPRA_API_KEY`, `OPRA_API_SECRET` et `OPRA_ACCOUNT_OR_SESSION`, chargés comme
`SecretStr` et jamais sérialisés.

Commande de finalisation/contrôle du contrat :

```bash
ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml
```

Cette commande ne se connecte pas et ne démarre pas la Phase M. Elle reconstruit les
preuves agrégées et valide uniquement la forme de la configuration. Le provider réel
implémentera `LiveOptionMarketDataProvider`, limité à `health()` et
`get_option_chain()`.

## Protocole prospectif à exécuter après validation humaine

1. Vérifier entitlement, licence, stockage, redistribution et limites de taux.
2. Capturer la chaîne live, le spot, le bid/ask, les timestamps provider/réception,
   la fraîcheur, le spread, le volume, l'open interest et les Greeks disponibles.
3. Recalculer les métriques lorsque le provider ne les fournit pas, sans masquer leur
   provenance.
4. Geler l'univers de candidats, les cinq scores, les métriques brutes, la
   classification, le candidat sélectionné, la meilleure baseline, le no-position,
   les prédictions et leurs intervalles dans un `PaperDecisionRecord` hash-chaîné.
5. Ne saisir le chemin réalisé qu'ultérieurement dans un `PaperRealizationRecord`
   séparé : entrée paper, sortie paper, slippage, frais, P&L et postmortem.
6. Comparer V10 aux mêmes baselines sur les mêmes timestamps et coûts.
7. Surveiller calibration, Brier/log-loss lorsque définis, rang, CVaR, pertes sévères,
   qualité des fills simulés, rejets, trous de données et changements de régime.
8. Appliquer purge/embargo et ne jamais retuner sur le holdout final après ouverture.
9. Produire un rapport Phase M distinct soumis à validation humaine.

## Critères de blocage immédiat

- entitlement non confirmé ;
- timestamp absent, quote trop vieille ou chaîne incomplète ;
- bid/ask croisé, contrat non standard non traité ou multiplicateur inconnu ;
- frais, slippage ou FX manquants ;
- hash de snapshot/decision invalide ;
- tentative de réécrire une décision après résultat ;
- incapacité à construire les mêmes baselines ;
- toute tentative de submit, modify, cancel, exercise ou roll.

## Invariants permanents

```text
read_only=true
transmit=false
what_if=true
order_capability=forbidden
```

Le preview IBKR peut vérifier contrat, combo, commission et marge what-if si disponible.
Il ne constitue jamais une autorisation de transmission.

## Sources officielles vérifiées le 18 août 2026

- [IBKR — TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR — market data permissions](https://ibkrcampus.com/campus/trading-lessons/trade-permissions-mkt/)
- [IBKR — market data subscriptions](https://ibkrcampus.com/docs/general/market-data-subscriptions/introduction)
- [OPRA — fee schedule](https://cdn.opraplan.com/documents/OPRA_Fee_Schedule.pdf)
- [OPRA — subscriber agreement, Exhibit A](https://cdn.opraplan.com/documents/OPRA_Exhibit_A.pdf)

Ces sources décrivent le mécanisme et les accords publics. Elles ne confirment pas les
droits, frais ou permissions du compte de l'utilisateur.
