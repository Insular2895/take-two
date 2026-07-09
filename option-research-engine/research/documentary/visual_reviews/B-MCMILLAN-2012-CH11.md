# Revue visuelle — B-MCMILLAN-2012 — Chapitre 11

Source : Lawrence G. McMillan, *Options as a Strategic Investment*, 5e édition.

Chapitre : 11 — Ratio Call Spreads.

Statut : `partial`

Date de revue : 2026-07-06.

Périmètre reçu : pages imprimées `210–211`, début du chapitre uniquement.

## Construction initiale

Exemple de ratio call spread `1 × 2` :

- achat d'un call avril `40` à `5` ;
- vente de deux calls avril `45` à `3` ;
- crédit initial `1`.

La structure possède :

- un gain limité sous le strike bas lorsque le crédit initial est positif ;
- un profit maximal au strike des calls vendus ;
- un risque théoriquement illimité au-dessus du break-even haut, car un call short reste découvert.

Formules données :

- points de profit maximal = crédit initial + écart entre strikes ;
- break-even haut = strike supérieur + points de profit maximal.

Dans l'exemple :

- profit maximal `6` au strike `45` ;
- break-even haut `51`.

## Impact projet

Cette structure ne doit pas être confondue avec un bull spread à risque borné. Le moteur doit
identifier explicitement :

- quantité nette de calls découverts ;
- risque de hausse non borné ;
- marge et assignation ;
- break-even haut ;
- interdiction éventuelle selon le mandat de risque.

## Limite de revue

Seules les deux premières pages sont reçues. Le chapitre complet va jusqu'à la page imprimée `221`.
