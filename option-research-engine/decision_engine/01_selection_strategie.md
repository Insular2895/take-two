# Sélection de stratégie

## 1. Règle fondamentale — aucune structure imposée

Le moteur ne doit **jamais** être forcé de proposer 1 à 3 Calls selon une logique fixe
« proche / moyen / éloigné ». Ce découpage n'est qu'un **exemple** de répartition possible,
pas une règle du système.

Le moteur analyse **toutes les combinaisons disponibles** et propose la ou les meilleures
structures selon :

- les règles extraites des livres ;
- les données de marché ;
- les Greeks ;
- la volatilité implicite ;
- la liquidité ;
- le budget ;
- les scénarios Monte Carlo ;
- le ratio rendement / risque.

La sortie peut donc être : un seul Call ; deux Calls ; trois Calls ; un Call ITM ; un Call ATM ;
un Call OTM ; un Call spread ; ou toute autre structure optionnelle si les règles extraites la
jugent supérieure. Le nombre de positions, leur répartition et leur distance au cours actuel sont
des **résultats de l'optimisation**, jamais des entrées.

> **Règle corrigée (officielle)** : le logiciel doit proposer la meilleure combinaison disponible
> selon les règles validées par la littérature et les simulations, sans imposer à l'avance le
> nombre de positions ni leur distance au cours actuel.

## 2. Génération de l'espace des candidats

Dimensions explorées automatiquement : strikes disponibles × échéances disponibles ×
répartitions du budget × tailles de position × règles de vente × trailing stops ×
règles de récupération du capital × règles de rolling × structures (Call sec, spread, combinaisons).

## 3. Élagage par les règles

Avant simulation, l'espace est réduit par les règles `ACTIVE` de type filtre
(ex. liquidité minimale, spread bid/ask maximal, open interest minimal — toutes issues de la
littérature, jamais arbitraires). Chaque élimination est journalisée avec la règle responsable.

## 4. Pipeline

`Candidats → Filtres (règles) → Simulation (MC + déterministe) → Scoring → Vote/conflits → Classement`.
