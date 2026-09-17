# Protocole de branchement IBKR

## Objectif

`ttwo-options data ibkr-validate` est la commande unique destinée au futur branchement. Elle ne
cherche pas à démontrer que le moteur gagne de l'argent. Elle fabrique un certificat borné de ce
qui a réellement été lu auprès d'IBKR, en conservant les échecs et les inconnus.

## Ce que la commande fait

```text
consentement --connect-read-only
  -> configuration paper/loopback + gates entitlement/licence
  -> health session 1
  -> health session 2 indépendante
  -> qualification TTWO + chaîne bornée
  -> rapport identité/complétude/volume/OI/Greeks/timestamps/type
  -> BAG optionnelle résolue depuis expiration/strike/type
  -> comparaison BAG/synthétique
  -> JSON strict + Markdown humain + snapshots privés
```

Chaque opération du transport officiel ouvre puis ferme sa session. Le deuxième health prouve que
deux sessions consécutives peuvent être établies. Il ne simule pas encore une perte réseau au
milieu d'une collecte : ce test opérateur reste nécessaire.

## Plan BAG

Le plan ne contient pas de `conId`, car celui-ci doit venir de la qualification réelle :

```json
{
  "schema_version": "1.0",
  "candidate_id": "structure-connue",
  "ticker": "TTWO",
  "legs": [
    {
      "expiration": "2027-01-15",
      "strike": 240.0,
      "option_type": "CALL",
      "action": "BUY",
      "ratio": 1,
      "exchange": "SMART"
    },
    {
      "expiration": "2027-01-15",
      "strike": 260.0,
      "option_type": "CALL",
      "action": "SELL",
      "ratio": 1,
      "exchange": "SMART"
    }
  ],
  "maximum_quote_age_seconds": 30,
  "example_only": false
}
```

Le fichier commité reste `example_only=true` : il est pédagogique et ne doit pas être lancé sans
vérifier que ses jambes existent. Le validateur exige une correspondance unique dans la chaîne,
puis injecte `conId`, bid et ask qualifiés dans la requête BAG.

Avant même le premier appel `health`, le validateur refuse un plan d'exemple, un ticker différent,
une expiration hors fenêtre, un strike hors fenêtre ou deux jambes désignant le même contrat. Ce
préflight évite d'ouvrir une socket pour une demande déjà invalide.

## Statuts du rapport

| Statut | Sens exact |
|---|---|
| `FAILED_SAFE` | Un contrôle demandé a échoué ; aucune promotion ni suite automatique. |
| `CAPTURED_NOT_PROMOTABLE` | Le chemin broker a répondu, mais une preuve stricte manque. |
| `CHAIN_PROMOTION_ELIGIBLE` | La chaîne satisfait les gates de données stricts ; BAG non demandée ou non confirmée. |
| `CHAIN_AND_COMBO_PROMOTION_ELIGIBLE` | Chaîne stricte et comparaison BAG fraîche/live/convention confirmée. |

« Promotion » signifie ici uniquement que l'artefact de données peut entrer dans l'étape suivante.
Cela ne valide pas l'entitlement, la licence, les modèles, une position, le paper ou l'exécution.

## Artefacts

Tous restent sous `reports/private/`, ignoré par Git :

- `ibkr-validation.json` : contrat machine, checks et codes ;
- `ibkr-validation.md` : lecture opérateur ;
- `ibkr-chain.json` : chaîne stricte ;
- `ibkr-market-snapshot.json` : conversion canonique moteur ;
- `ibkr_combo_validation.json` : sélection humaine locale des jambes.

Le rapport ne sérialise ni identifiant de compte, ni host, ni client ID, ni credential.

## Ce qui se passe après

Rien automatiquement. L'opérateur compare plusieurs contrats à TWS, documente les codes et les
écarts, valide la convention BAG, puis décide séparément si le checkpoint peut être classé. Shadow,
paper, what-if et exécution restent bloqués.
