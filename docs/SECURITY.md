# Sécurité et frontière d’exécution

## Invariants

- aucune soumission, modification, annulation ou exercice d’ordre ;
- `transmit=false`, `what_if=true`, `order_capability=forbidden` et confirmation
  humaine obligatoire ;
- connecteurs live désactivés par défaut et injectés comme ports read-only ;
- aucune clé dans le dépôt, les rapports, l’HTML ou les logs ;
- erreur réseau fail-closed et données manquantes jamais remplacées ;
- HTML V11 autonome, sans requête réseau ni calcul financier côté client ;
- fixtures toujours marquées `synthetic` et non promouvables.

Le test `assert_all_execution_paths_forbidden()` inspecte tous les fichiers Python du
package pour les imports/constructeurs d’ordre interdits et `transmit=True`. Le script
`scripts/security_gate.py` ajoute un scan de secrets à haute confiance et de capacités
réseau dans les rapports HTML V11.

## Exécution locale

```bash
python scripts/security_gate.py
pytest -q
```

Les fichiers `.env*` sont ignorés par Git, sauf exemple sans secret. Le scanner vérifie
les fichiers suivis sans afficher le contenu d’un environnement local.

## Limites

Ce contrôle statique ne remplace pas une revue indépendante, un threat model, du SAST,
une analyse de dépendances, une rotation de secrets ou un test d’intrusion. Ces preuves
sont exigées avant le gate commercial.
