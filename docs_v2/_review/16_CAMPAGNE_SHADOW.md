# Contrôle de campagne shadow

## Pourquoi cette couche existe

Une chaîne IBKR correcte ne prouve pas que le moteur prend de bonnes décisions. Avant tout paper
trading, il faut observer prospectivement ce que le bot aurait décidé, puis attendre le résultat
futur sans réécrire la décision. Le contrôle shadow prépare cette preuve. Il ne crée aucune
position, réelle ou paper.

## Les trois objets à ne pas confondre

```text
ShadowCampaignManifest
  fixe période + seuils + commit + config + preuves + approbations
          |
          v
PaperDecisionRecord (journal 1)
  fige ce que le moteur savait et choisissait à l'instant t
          |
          v plus tard seulement
PaperRealizationRecord (journal 2)
  rattache le chemin observé au hash exact de la décision
```

Le manifeste répond à « selon quelles règles mesure-t-on ? ». La décision répond à « qu'aurait
fait le moteur sans connaître l'avenir ? ». La réalisation répond à « qu'est-il arrivé ensuite ? ».
Séparer ces objets empêche d'ajuster rétrospectivement une décision après avoir vu le résultat.

## Pourquoi il n'existe aucun seuil par défaut

La durée, le nombre minimal de décisions, le nombre minimal de réalisations et les délais maximaux
d'enregistrement relèvent du responsable risque. Les coder arbitrairement transformerait une
hypothèse en décision. Le manifeste d'exemple porte donc :

```text
approval_status=draft_to_validate
thresholds=null
example_only=true
```

Pour devenir `approved`, une copie privée doit fournir :

- les seuils explicitement validés ;
- le commit et le hash de configuration gelés ;
- le hash du rapport de validation IBKR ;
- le hash du ledger holdout ;
- une référence d'approbation des droits data ;
- une référence d'approbation du responsable risque ;
- `example_only=false`.

Une valeur manquante fait échouer la validation du manifeste avant toute campagne.

## Propriétés des journaux

Chaque ligne contient un numéro de séquence, le hash de la ligne précédente et son propre hash.
Elle contient aussi `campaign_id` et `recorded_at`. L'ajout vérifie la tête attendue avant écriture.
Le chargeur ou le contrôle refuse :

- une séquence manquante ou déplacée ;
- une ligne modifiée ;
- un identifiant réutilisé ;
- une réalisation reliée à une décision inconnue ou à un mauvais hash ;
- deux réalisations finales pour la même décision ;
- une entrée paper antérieure à la décision ;
- une sortie antérieure à l'entrée ou une observation antérieure à la sortie.
- un brouillon marqué `example_only` ;
- une campagne, un commit ou une configuration différents ;
- une décision hors fenêtre ;
- un délai entre décision/observation et écriture supérieur au seuil approuvé.

Les fichiers privés sont prévus sous `reports/private/`, ignoré par Git. Un hash protège
l'intégrité ; il ne chiffre pas les données et ne remplace pas les contrôles d'accès.

`PaperDecisionRecord` est en version `1.1` et `PaperRealizationRecord` en version `1.2` pour porter
la campagne et l'heure réelle d'écriture. Aucune campagne réelle n'existait avant cette évolution ;
elle ne réécrit donc aucun journal de campagne.

## États du rapport

| État | Sens exact |
|---|---|
| `BLOCKED_DRAFT` | Manifeste non approuvé ou exemple ; rien ne doit commencer. |
| `READY_TO_START` | Contrôle prêt, période future, aucune observation enregistrée. |
| `IN_PROGRESS` | Période active, cibles non atteintes. |
| `OBSERVATION_TARGET_REACHED_PENDING_HUMAN_REVIEW` | Cibles de comptage atteintes ; revue qualitative encore obligatoire. |
| `WINDOW_ENDED_INCOMPLETE` | Période terminée sans atteindre les cibles. |
| `FAILED_SAFE` | Drift de commit/config, décision hors fenêtre ou intégrité invalide. |

Dans tous les états :

```text
paper_validation_passed=false
promotion_eligible=false
transmit=false
order_capability=forbidden
human_review_required=true
```

Le rapport compte aussi `NO_POSITION`. Ne pas trader est une vraie décision prospective et doit
rester visible ; l'exclure gonflerait artificiellement l'activité et biaiserait l'évaluation.

## Commande de contrôle

```bash
ttwo-options paper shadow-status \
  --manifest configs/paper/shadow_campaign.example.json \
  --decision-ledger reports/private/paper-decisions.jsonl \
  --realization-ledger reports/private/paper-realizations.jsonl \
  --output reports/private/shadow-campaign-status.json
```

Sur l'exemple commité, `BLOCKED_DRAFT` et un code de sortie non nul sont attendus. Cette commande
ne collecte pas de données, ne contacte pas IBKR et n'ajoute aucune ligne aux journaux. La future
campagne doit appeler les commandes append-only au moment réel de la décision, jamais reconstruire
les décisions a posteriori :

```bash
ttwo-options paper append-shadow-decision \
  --manifest reports/private/shadow-campaign.json \
  --draft reports/private/next-paper-decision.json

ttwo-options paper append-shadow-realization \
  --manifest reports/private/shadow-campaign.json \
  --draft reports/private/next-paper-realization.json
```

Les modèles de brouillon commités sont volontairement `example_only=true`. Ils montrent la forme,
mais ne peuvent pas alimenter une campagne approuvée.

## Ce qui reste réellement à faire

1. Valider entitlement/licence et exécuter le protocole IBKR read-only.
2. Franchir les gates historique/walk-forward et ouvrir le holdout selon sa procédure séparée.
3. Faire valider les seuils et la période par le responsable risque.
4. Déclencher l'append au moment réel de chaque sortie du moteur gelé.
5. Collecter données manquantes, incidents, coûts, slippage et réalisations futures.
6. Réaliser la revue humaine finale.

Même après ces étapes, l'exécution reste un projet et une décision séparés.
