# Holdout final frais — phase F

Le registre canonique est `validation/final_holdout_ledger.jsonl`. Son état est
`UNOPENED`. L'entrée initiale ne possède aucun `dataset_hash` : elle initialise la
machine d'état sans ouvrir, sélectionner ou même identifier des observations.

Procédure future :

1. acquérir un dataset autorisé et vérifier son intégrité point-in-time ;
2. figer code, configuration, formules de scores, seuils, modèles et coûts ;
3. ajouter un événement `provision` avec le hash immuable du dataset ;
4. vérifier le head hash attendu avant toute écriture ;
5. réaliser une unique transition `open_once` vers `OPENED_ONCE` ;
6. publier le résultat inchangé via `report_unchanged`, sans retuning.

Une seconde ouverture est impossible. Un changement de `holdout_id` ou de hash est
refusé. `CONTAMINATED` et `INVALID` sont terminaux. La chaîne hashée détecte une ligne
modifiée, supprimée, réordonnée ou insérée. Le fichier est append-only ; l'API
d'écriture utilise un head hash attendu pour refuser une mise à jour concurrente
obsolète.

Les jeux V7, V8, V9 et toutes les données déjà inspectées restent impropres au holdout.
Le run walk-forward de phase E n'a pas touché ce registre. Aucun statut
`holdout_validated` n'est actuellement permis.
