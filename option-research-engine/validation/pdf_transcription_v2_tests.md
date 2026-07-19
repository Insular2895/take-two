# Plan de validation — transcription PDF technique V2

Statut : `draft_to_validate`  
Spécification : `../docs/07_transcription_pdf_technique_v2.md`

## 1. Critère principal

Le test prioritaire est le nombre d'erreurs quantitatives dangereuses acceptées sans alerte.
Une erreur dangereuse comprend notamment : signe, décimale, fraction, quantité, colonne, unité,
Greek, volatilité, débit/crédit, payoff, break-even ou formule mal associés.

Objectif du golden set : `0` erreur dangereuse acceptée.

## 2. Golden set minimal

| ID | Cas |
|---|---|
| G01 | texte natif propre |
| G02 | scan propre |
| G03 | scan incliné |
| G04 | faible contraste |
| G05 | tableau tourné à 90 degrés |
| G06 | en-têtes multi-niveaux |
| G07 | décimales signées |
| G08 | fractions |
| G09 | formules avec fraction/exposant |
| G10 | payoff diagram |
| G11 | graphique multi-séries |
| G12 | annotations externes rouges |
| G13 | page PDF différente de la page imprimée |
| G14 | tableau continué |
| G15 | caption sur page précédente |
| G16 | panne Gemini |
| G17 | JSON Gemini invalide |
| G18 | désaccord Gemini/OCR |
| G19 | média indisponible dans le runtime Codex |

Les extraits doivent être locaux et réduits au minimum nécessaire pour respecter les droits des
ouvrages. Les livres complets ne sont jamais intégrés aux fixtures Git.

## 3. Tests unitaires obligatoires

- conservation exacte de `+` et `-` ;
- distinction `.0060` / `-.0060` ;
- distinction `0.6` / `0.06` / `0.006` ;
- conservation de `1/2`, `3/4` et des fractions typographiques ;
- bbox de quatre coordonnées dans le bon repère ;
- rotation 90/180/270 et inversion correcte du repère ;
- association exacte en-tête/cellule ;
- cellule vide distincte de zéro ;
- continuation de tableau sans duplication de lignes ;
- formule avec fraction et parenthèses ;
- calcul visible `+20 × .13` ;
- calcul visible `-30 × .100` ;
- pagination PDF/imprimée distincte ;
- figure extraite mais `data_digitized=false` ;
- annotation rouge classée comme artefact et non comme contenu source ;
- refus d'un statut validé en présence d'un désaccord critique.

## 4. Test Gemini minimal

1. rendre une page connue ;
2. découper un tableau connu ;
3. envoyer page et crop, avec leurs métadonnées ;
4. exiger un JSON strict ;
5. valider le schéma ;
6. vérifier que les médias figurent réellement dans la requête ;
7. enregistrer la réponse dans le paquet de preuve ;
8. comparer sans modifier le sidecar ;
9. simuler timeout, quota, média refusé et JSON invalide ;
10. vérifier le déclenchement du fallback.

## 5. Test fallback Codex

Vérifier que la commande d'inspection :

- existe et retourne un code explicite ;
- génère page, crop, normalisation et contexte attendus ;
- affiche page PDF et page imprimée ;
- retourne les chemins des preuves ;
- ne modifie pas le PDF ;
- ne modifie pas le Markdown ;
- écrit une revue séparée ;
- gère `codex_media_unavailable` ;
- ne promeut pas une ambiguïté persistante.

## 6. Tests d'intégration

- exécution répétée idempotente ;
- reprise après interruption ;
- invalidation du cache après changement de DPI, bbox, OCR, prompt ou schéma ;
- paquet partiellement écrit non considéré comme terminé ;
- run complet avec Gemini désactivé ;
- run complet avec quota Gemini atteint ;
- rapport final cohérent avec les sidecars ;
- aucune fuite de clé, chemin sensible ou PDF dans Git ;
- règle de recherche refusée si sa source est `blocked`, `unextractable` ou `image_only`.

## 7. Métriques secondaires

- taux de détection des éléments complexes ;
- taux de faux blocages ;
- taux de revues visuelles résolues ;
- couverture des cellules critiques ;
- latence par page et par type ;
- coût Gemini par livre ;
- taux de réutilisation du cache ;
- volume de revue humaine restant.

## 8. Rapport de non-régression

Toute version doit publier localement :

```text
pipeline_version
golden_set_version
schema_versions
prompt_versions
pages_tested
critical_elements_tested
dangerous_errors_accepted
blocking_alerts_expected_vs_observed
false_blocks
latency
remote_cost
result: pass | fail
```

La livraison échoue si `dangerous_errors_accepted > 0`.
