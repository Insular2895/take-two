# What-if hors ligne et preuve de résilience

## Pourquoi le what-if est traité à part

IBKR documente la prévisualisation de marge comme un `Order` portant `WhatIf=true`, envoyé par
`placeOrder`, puis retourné dans un `OrderState`. IBKR indique que cet ordre what-if n'est pas routé,
mais l'appel appartient tout de même à une primitive capable de placer des ordres. L'adaptateur de
marché de ce dépôt ne l'importe donc pas et ne l'appelle pas.

Cette séparation est volontaire : « non routé par le broker » n'est pas équivalent à « absent de
la frontière ordre du logiciel ». Une future procédure dédiée pourra obtenir ce preview sous
contrôle humain. Le code présent ne fait qu'assainir la réponse ensuite, hors ligne.

## Le flux exact

```text
procédure broker séparée et approuvée
  -> transcription redacted BrokerWhatIfObservation
  -> paper what-if-normalize (aucune connexion)
  -> BrokerWhatIfEvidence + rapport de normalisation
  -> preview moteur, seulement si preuve complète/candidat identique/USD
```

Le fichier d'entrée peut contenir les chaînes brutes de commission, marges initiale/maintenance et
equity-with-loan avant/changement/après. Il ne doit contenir aucun numéro de compte. Le texte brut
d'avertissement n'est jamais recopié dans la preuve : seul
`WHAT_IF_BROKER_WARNING_PRESENT_REDACTED` subsiste.

## Règles de normalisation

| Entrée | Traitement |
|---|---|
| vide ou absente | `null` + code `MISSING` |
| non numérique | `null` + code `INVALID` |
| NaN/infini | `null` + code `NON_FINITE` |
| valeur sentinelle énorme | `null` + code `SENTINEL` |
| commission négative | `null` + code `NEGATIVE` |
| bornes de commission incohérentes | preuve incomplète |
| devise commission absente/différente | preuve incomplète |

`complete=true` exige au minimum commission, changement de marge initiale, changement de marge de
maintenance et devise de commission identique. `buying_power_change` reste `null` : le code ne le
déduit pas d'equity-with-loan. Une marge signée reste signée ; elle n'est ni mise en valeur absolue
ni transformée en capital requis.

## Commande offline

```bash
cp configs/opra/ibkr_what_if_observation.example.json \
  reports/private/ibkr-what-if-observation.json

ttwo-options paper what-if-normalize \
  --observation reports/private/ibkr-what-if-observation.json \
  --evidence-out reports/private/ibkr-what-if-evidence.json \
  --report-out reports/private/ibkr-what-if-normalization.json
```

Le modèle commité porte `example_only=true` et échoue volontairement. Une observation réelle doit
être redacted, datée, rattachée à un candidat gelé et mise à `example_only=false`. Un rapport
`NORMALIZED_INCOMPLETE` est écrit pour rendre les inconnues visibles, puis la commande retourne un
code non nul.

## Retry, pacing et cache : ce qui devient prouvable

`IbkrProviderDiagnostics` conserve uniquement des compteurs :

- opérations de lecture et tentatives transport ;
- erreurs transitoires et retries épuisés ;
- nombre et durée des attentes de pacing ;
- hits, misses et expirations du cache ;
- `stale_fallbacks=0` par contrat.

Ces compteurs entrent dans le JSON et le Markdown de `ibkr-validate`. Ils permettent de distinguer
« une lecture a réussi du premier coup », « un retry a été nécessaire » et « les retries ont été
épuisés ». Ils ne prouvent une reconnexion réelle que lorsque le rapport vient d'une session IBKR
archivée avec ses logs redacted.

## Ce qui reste à prouver après connexion

- valeurs exactes réellement renvoyées par `OrderState` selon la structure OPT/BAG ;
- support ou non du what-if pour chaque smart combo ciblée ;
- convention des changements de marge et devise dans le compte paper ;
- codes d'erreur et avertissements, sans exposer le compte ;
- pacing réel, coupure au milieu d'une collecte et reprise contrôlée ;
- cohérence commission/marge entre preview et éventuelle exécution paper future.

Même une preuve complète conserve `transmit=false`, `order_capability=forbidden` et
`strategy_promotion_eligible=false`.

## Sources IBKR vérifiées le 17 septembre 2026

- documentation TWS API actuelle : <https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/> ;
- page officielle historique détaillant le mécanisme what-if :
  <https://interactivebrokers.github.io/tws-api/margin.html> ;
- champs `OrderState` :
  <https://interactivebrokers.github.io/tws-api/classIBApi_1_1OrderState.html>.

Les deux dernières pages sont marquées comme documentation historique par IBKR. Elles servent à
expliquer la sémantique précise observée ; la procédure de connexion devra revérifier la
documentation Campus et le comportement de la version TWS/IB Gateway réellement installée.
