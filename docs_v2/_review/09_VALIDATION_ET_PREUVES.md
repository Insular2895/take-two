# Validation et niveaux de preuve

## Pyramide de preuve

| Niveau | Ce qu’il prouve | Ce qu’il ne prouve pas |
|---|---|---|
| Schéma/type | Forme et contraintes | Qualité du marché |
| Test unitaire | Fonction locale | Intégration broker |
| Test d’intégration fake | Flux logiciel déterministe | Callbacks réels |
| Fixture/replay | Reproductibilité | Rentabilité |
| Historique réel | Comportement passé sous hypothèses | Futur |
| Walk-forward | Généralisation limitée | Fill réel |
| Live read-only | Données et connectivité | Exécution |
| Shadow | Décisions prospectives sans effet | Fill |
| Paper | Interaction broker simulée | Risque monétaire réel |

## Gates logiciels

Les commandes de validation sont :

```bash
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pytest -q
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/validate_research_registry.py
.venv/bin/python scripts/security_gate.py
cd cloudflare && npm run check
cd services/ibkr-paper-bridge && PYTHONPATH=src ../../.venv/bin/python -m pytest -q
```

Un gate vert signifie que le dépôt respecte les contrats testés à cet instant. Il ne change pas
automatiquement `OPRA_ENTITLEMENT_CONFIRMED`, `OPRA_LICENSE_REVIEWED`, le holdout ou le statut paper.

La commande future `ttwo-options data ibkr-validate` produit en plus un rapport JSON strict et un
rapport Markdown. Elle contrôle deux sessions indépendantes, la chaîne et, si un plan est fourni,
une BAG. Voir [le protocole de branchement](15_PROTOCOLE_BRANCHEMENT_IBKR.md).

La commande offline `ttwo-options paper shadow-status` vérifie ensuite le manifeste et les deux
journaux prospectifs. Elle ne lance ni provider ni paper trading et ne peut pas produire
`paper_validation_passed=true`. Voir [le contrôle shadow](16_CAMPAGNE_SHADOW.md).

## Validation réelle minimale du nouveau provider

À effectuer après validation humaine :

1. handshake sur IB Gateway paper ;
2. qualification unique de TTWO ;
3. capture d’une petite plage d’expirations et de strikes ;
4. contrôle manuel de plusieurs `conId` dans IB Gateway ;
5. contrôle bid/ask, type live/delayed, volume, OI et Greeks ;
6. contrôle timestamps provider/réception ;
7. répétition après déconnexion/reconnexion ;
8. élargissement progressif pour observer pacing et timeouts ;
9. quote BAG d’une structure connue ;
10. comparaison avec l’affichage TWS et validation de la convention signée.

Le contrôle automatisé de « seconde session indépendante » ferme puis rouvre une opération
broker. Il ne remplace pas encore un test opérateur de coupure réseau au milieu d'une collecte.

## Promotion

La promotion du snapshot exige aujourd’hui découverte complète, collecte complète, aucune quote
manquante, type `live` et timestamp provider/exchange. C’est volontairement strict. Une future
politique plus nuancée devra être validée sur des observations réelles ; elle ne doit pas être
assouplie uniquement pour faire passer un run.
