# benchmarks/ — Résultats comparatifs

## Rôle
Stocker les comparaisons OBJECTIVES : stratégie vs stratégie, notre implémentation vs état de
l'art open source, méthode numérique vs méthode numérique.

## Ce qui y sera stocké
- Cas canoniques de pricing/simulation (valeurs de référence issues des repos étudiés, à
  reproduire par nos futurs composants — cf. `research/benchmarks/financial-models-numerical-methods.md`).
- Comparaisons de composants candidats (précision, vitesse, robustesse) justifiant intégration ou rejet.
- Comparaisons de stratégies issues du moteur (quand il existera), pour audit du scoring.

## Format attendu
Un fichier par benchmark : Question / Candidats / Protocole / Métriques / Résultats / Décision.

## Conventions
Aucun composant n'est adopté « parce qu'il est populaire » : le benchmark est la preuve exigée.

## Dépendances
`research/benchmarks/`, `validation/`, `monte_carlo/`.
