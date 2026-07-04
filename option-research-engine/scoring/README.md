# scoring/ — Moteur de scoring

## Rôle
Spécifier et sourcer le score : composants (espérance, probabilité, risque, liquidité, coût,
robustesse), normalisations, pondérations et leur calibration.

## Ce qui y sera stocké
- Définition officielle de chaque composant (formule, données, règles sources).
- Versions successives des pondérations avec leur justification et leur validation.
- Exigences de reproductibilité et de décomposabilité du score.

## Format attendu
Un fichier par composant + un fichier `ponderations_vN.md` par version.

## Conventions
Toute pondération est versionnée ; aucune constante sans source (littérature ou calibration validée).

## Dépendances
`decision_engine/04_scoring.md` (spécification maîtresse), `rules/DECISION/`, `validation/`.
