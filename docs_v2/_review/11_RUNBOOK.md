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
ttwo-options data ibkr-validate \
  --expiration-start 2027-01-01 \
  --expiration-end 2027-02-01 \
  --minimum-strike 180 \
  --maximum-strike 320 \
  --maximum-contracts 500 \
  --maximum-expirations 12 \
  --report-json-out reports/private/ibkr-validation.json
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

## 4. Préparer éventuellement une BAG connue

Copier le modèle, choisir des jambes réellement présentes dans la plage de chaîne, puis remplacer
`example_only` par `false` :

```bash
cp configs/opra/ibkr_combo_validation.example.json \
  reports/private/ibkr_combo_validation.json
```

Le modèle est volontairement bloqué tant qu'il reste `example_only=true`. Le validateur résout les
`conId` depuis expiration, strike et type ; il refuse une jambe absente ou ambiguë.

## 5. Commande unique de validation future

Après validation humaine, IB Gateway Paper connecté et Read-Only activé :

```bash
ttwo-options data ibkr-validate \
  --connect-read-only \
  --expiration-start 2027-01-01 \
  --expiration-end 2027-02-01 \
  --minimum-strike 180 \
  --maximum-strike 320 \
  --maximum-contracts 500 \
  --maximum-expirations 12 \
  --maximum-quote-age-seconds 30 \
  --combo-plan reports/private/ibkr_combo_validation.json \
  --report-json-out reports/private/ibkr-validation.json \
  --report-markdown-out reports/private/ibkr-validation.md \
  --chain-json-out reports/private/ibkr-chain.json \
  --engine-json-out reports/private/ibkr-market-snapshot.json
```

Commencer avec une petite plage. Élargir seulement après observation du nombre de contrats, des
timeouts et des codes IBKR. Pour une première exploration sans BAG, omettre `--combo-plan` ; le
rapport inscrira explicitement `NOT_RUN`.

## 6. Interpréter le résultat

- `CAPTURED_NOT_PROMOTABLE` est normal pour delayed ou timestamp client ;
- `CHAIN_PROMOTION_ELIGIBLE` ne valide que les données, pas la stratégie ou la licence ;
- `CHAIN_AND_COMBO_PROMOTION_ELIGIBLE` exige aussi fraîcheur et convention BAG confirmées ;
- `FAILED_SAFE` conserve le code d'échec redacted et ne démarre rien d'autre ;
- `missing_quote_count>0` interdit de déclarer la collecte complète ;
- `IBKR_CHAIN_EXCEEDS_MAXIMUM_CONTRACTS` demande de réduire la plage, pas d’augmenter aveuglément ;
- `OPRA_ENTITLEMENT_NOT_CONFIRMED` ou `OPRA_LICENSE_NOT_REVIEWED` est un gate humain ;
- `OFFICIAL_IBAPI_NOT_INSTALLED` signifie que le client officiel doit être installé dans le même
  environnement Python ;
- aucune erreur ne doit conduire à un fallback synthétique promu.

## 7. Arrêt

Après la première capture, ne pas démarrer automatiquement shadow ou paper. Archiver le log
redacted, comparer plusieurs contrats à TWS, documenter les écarts et faire valider le checkpoint.

## 8. Préparer le contrôle shadow sans démarrer de campagne

Le manifeste commité est volontairement un brouillon bloqué :

```bash
ttwo-options paper shadow-status \
  --manifest configs/paper/shadow_campaign.example.json \
  --decision-ledger reports/private/paper-decisions.jsonl \
  --realization-ledger reports/private/paper-realizations.jsonl \
  --output reports/private/shadow-campaign-status.json
```

Avec le fichier d'exemple, la commande écrit `BLOCKED_DRAFT` puis sort en erreur. C'est le résultat
attendu : elle ne contacte aucun provider et ne démarre aucune activité paper. Une copie privée ne
peut devenir `approved` que si le responsable renseigne les seuils, la période, le commit, le hash
de configuration, les preuves IBKR/holdout, les droits data et sa référence d'approbation.

Le statut le plus avancé reste `OBSERVATION_TARGET_REACHED_PENDING_HUMAN_REVIEW` avec
`paper_validation_passed=false`. Il n'existe aucune transition automatique vers l'exécution.
