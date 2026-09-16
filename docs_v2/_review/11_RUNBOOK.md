# Runbook : travailler offline puis connecter plus tard

## 1. Validation entièrement offline

Depuis la racine :

```bash
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pytest -q
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/security_gate.py
```

Bridge et Worker :

```bash
cd services/ibkr-paper-bridge
PYTHONPATH=src ../../.venv/bin/python -m pytest -q

cd ../../cloudflare
npm run check
```

Ces commandes ne nécessitent pas IBKR.

## 2. Vérifier que la commande live reste désarmée

Sans le drapeau explicite, cette commande doit sortir avec « connection not attempted » :

```bash
ttwo-options data ibkr-chain \
  --expiration-start 2027-01-01 \
  --expiration-end 2027-02-01 \
  --minimum-strike 180 \
  --maximum-strike 320 \
  --maximum-contracts 500 \
  --maximum-expirations 12 \
  --json-out reports/private/ibkr-chain.json
```

## 3. Préparer l’environnement, sans connecter

Variables non secrètes attendues :

```text
OPRA_PROVIDER=ibkr_gateway
IBKR_HOST=127.0.0.1
IBKR_PORT=4002
IBKR_CLIENT_ID=<id dédié>
IBKR_SESSION_MODE=paper
IBKR_MARKET_DATA_TYPE=delayed
OPRA_ENTITLEMENT_CONFIRMED=false
OPRA_LICENSE_REVIEWED=false
```

Les deux dernières valeurs ne passent à `true` qu’après validation humaine. Le fichier de sortie
doit rester sous `reports/private/`, dossier ignoré par Git, s’il contient des données licenciées.

## 4. Commande unique de capture future

Après validation humaine, IB Gateway Paper connecté et Read-Only activé :

```bash
ttwo-options data ibkr-chain \
  --connect-read-only \
  --expiration-start 2027-01-01 \
  --expiration-end 2027-02-01 \
  --minimum-strike 180 \
  --maximum-strike 320 \
  --maximum-contracts 500 \
  --maximum-expirations 12 \
  --maximum-quote-age-seconds 30 \
  --json-out reports/private/ibkr-chain.json \
  --engine-json-out reports/private/ibkr-market-snapshot.json
```

Commencer avec une petite plage. Élargir seulement après observation du nombre de contrats, des
timeouts et des codes IBKR.

## 5. Interpréter le résultat

- `promotion_eligible=false` est normal pour delayed ou timestamp client ;
- `missing_quote_count>0` interdit de déclarer la collecte complète ;
- `IBKR_CHAIN_EXCEEDS_MAXIMUM_CONTRACTS` demande de réduire la plage, pas d’augmenter aveuglément ;
- `OPRA_ENTITLEMENT_NOT_CONFIRMED` ou `OPRA_LICENSE_NOT_REVIEWED` est un gate humain ;
- `OFFICIAL_IBAPI_NOT_INSTALLED` signifie que le client officiel doit être installé dans le même
  environnement Python ;
- aucune erreur ne doit conduire à un fallback synthétique promu.

## 6. Arrêt

Après la première capture, ne pas démarrer automatiquement shadow ou paper. Archiver le log
redacted, comparer plusieurs contrats à TWS, documenter les écarts et faire valider le checkpoint.
