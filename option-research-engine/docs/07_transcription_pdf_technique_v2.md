# Transcription PDF technique vers Markdown et JSON — Spécification V2

Statut : `draft_to_validate`  
Date : 2026-07-14  
Périmètre : extraction documentaire uniquement, sans recommandation ni exécution de trade.

## 1. Objectif

Le pipeline transforme des livres techniques locaux en quatre sorties liées :

1. un Markdown lisible ;
2. un JSON sidecar canonique ;
3. des preuves visuelles pour les éléments complexes ;
4. un rapport qualité et une file de revue.

Il doit détecter les paragraphes, tableaux, formules, figures, graphiques, payoff diagrams,
rotations et différences entre pagination PDF et pagination imprimée.

La métrique principale est le **taux d'erreurs quantitatives dangereuses acceptées sans alerte**.
La cible est zéro ; une donnée ambiguë doit rester ambiguë et ne jamais être complétée silencieusement.

## 2. Principes non négociables

- Le PDF original est local, immuable, en lecture seule et hors Git.
- La page rendue et son crop constituent la preuve documentaire primaire.
- Le texte natif, l'OCR, Gemini et Codex produisent des lectures candidates, pas une vérité autonome.
- Le JSON sidecar est canonique ; le Markdown est une vue dérivée.
- Les valeurs brutes restent conservées, même après normalisation.
- Aucun signe, chiffre, fraction, colonne, formule, unité ou numéro de page n'est corrigé sans trace.
- Un accord entre modèles ne neutralise jamais l'échec d'un contrôle déterministe.
- Aucun élément bloqué ne peut alimenter une règle quantitative `VALIDATED`.
- Les contenus protégés ne sont ni publiés intégralement ni envoyés inutilement à une API.

## 3. Architecture

```text
PDF local immuable
  -> manifeste et SHA-256
  -> analyse locale page par page
  -> extracteurs spécialisés
  -> contrôles déterministes
  -> vérification visuelle Gemini ciblée
  -> fallback Codex local ciblé si nécessaire
  -> Markdown + JSON + preuves + rapport + file de revue
```

### 3.1 Niveau 1 — extraction locale déterministe

Pour chaque page :

- extraire le texte natif s'il est exploitable ;
- rendre une image PNG à DPI documenté ;
- détecter orientation, rotation et skew ;
- lancer l'OCR lorsque le texte natif est absent ou insuffisant ;
- analyser le layout et segmenter les régions ;
- classer chaque région : texte, tableau, formule, figure, graphique, payoff diagram, artefact ;
- tenter l'extraction spécialisée ;
- exécuter les contrôles syntaxiques, arithmétiques et métier.

### 3.2 Niveau 2 — vérification visuelle Gemini

Gemini reçoit seulement des paquets de preuve ciblés. Il compare les médias à l'extraction
candidate et renvoie un JSON strict. Il ne reçoit pas le livre entier par défaut et ne valide pas
une règle de trading.

### 3.3 Niveau 3 — fallback Codex

Codex intervient lorsque Gemini est indisponible, invalide, insuffisamment confiant ou en désaccord
critique. Codex lance l'inspection locale, ouvre les mêmes preuves et écrit un rapport séparé. Il ne
modifie jamais directement la transcription quantitative.

## 4. Ingestion et manifeste

Chaque exécution doit produire un manifeste comprenant au minimum :

```json
{
  "document_id": "sha256prefix",
  "source_filename": "local-only.pdf",
  "pdf_sha256": "...",
  "page_count": 0,
  "pipeline_version": "2.0.0",
  "started_at": "RFC3339",
  "source_policy": "local_read_only"
}
```

Le chemin absolu du PDF peut figurer dans un manifeste local non versionné, mais pas dans une
sortie publique. Le pipeline refuse toute tentative de modification du fichier source.

## 5. Paquet de preuve

Chaque élément complexe obtient un identifiant stable et un dossier local :

```text
evidence_packets/<run_id>/<element_id>/
  full_page_original.png
  full_page_preprocessed.png
  element_crop_original.png
  element_crop_normalized.png
  previous_page.png             # si le contexte est requis
  next_page.png                 # si le contexte est requis
  extraction_candidate.json
  native_text.txt
  ocr_text.txt
  metadata.json
  gemini_review.json             # si appelé
  codex_review.json              # si fallback appelé
```

`metadata.json` conserve : document, page PDF, page imprimée, chapitre, section, type, bounding
box, rotation source/appliquée, DPI, alertes, versions du prompt et du schéma.

## 6. Déclenchement de la revue visuelle

Une revue Gemini est obligatoire si :

```python
element.type in {"table", "formula", "chart", "payoff_diagram"}
or element.rotation in {90, 180, 270}
or element.numeric_confidence < 0.95
or element.table_structure_confidence < 0.90
or sign_disagreement
or decimal_disagreement
or column_shift_risk
or arithmetic_check_failed
or formula_structure_ambiguous
```

Ces seuils sont des valeurs initiales conservatrices. Leur modification nécessite un test sur le
golden set et une décision documentée.

## 7. Contrat Gemini

Le prompt officiel est dans `../prompts/pdf_visual_verifier_gemini_v2.md`. La réponse doit respecter
`../schemas/gemini_visual_review.schema.json`.

Règles d'intégration :

1. envoyer page complète et crop précis ;
2. inclure l'extraction candidate et les alertes existantes ;
3. exiger du JSON sans texte libre ;
4. valider la réponse avec le schéma ;
5. permettre une seule tentative de réparation structurée ;
6. déclencher le fallback si la réparation échoue ;
7. archiver la réponse brute sans modifier automatiquement le sidecar final.

Gemini doit préserver exactement signes, décimales, fractions, exposants, parenthèses, unités,
quantités et associations colonne-valeur. En cas de doute, il retourne plusieurs candidats.

## 8. Fallback Codex et commande d'inspection

L'implémentation doit exposer une commande stable :

```bash
python -m pdf_transcriber.inspect \
  --pdf "sources/local-only/book.pdf" \
  --page 132 \
  --element p132-table-7-2 \
  --dpi 450 \
  --include-context auto \
  --open
```

La commande localise le PDF, rend la page, produit le crop, applique la rotation, ajoute le contexte
utile, écrit le paquet de preuve et retourne les chemins. Elle ne modifie ni le PDF ni le Markdown.

Le fallback écrit exclusivement un fichier de revue contenant les divergences visibles, lectures
candidates, zones illisibles et statut recommandé. Si le runtime ne peut pas ouvrir les images, le
statut devient `codex_media_unavailable`, puis `human_review_required`.

## 9. Ordre de décision

```text
Extraction locale suffisante et contenu non critique
  -> machine_verified

Contenu critique ou confiance insuffisante
  -> Gemini
     -> accord + seuils + contrôles réussis
        -> machine_verified_with_visual_check
     -> ambiguïté
        -> needs_visual_review
     -> erreur ou divergence critique
        -> Codex fallback
           -> conclusion visuelle traçable + contrôles réussis
              -> machine_reviewed
           -> ambiguïté persistante
              -> human_review_required ou blocked
```

La validation humaine est la seule voie permettant de résoudre une ambiguïté critique persistante.

## 10. JSON sidecar canonique

Le schéma de base est `../schemas/pdf_element_sidecar.schema.json`. Chaque cellule quantitative
conserve au minimum :

```json
{
  "raw_ocr": "-.0060",
  "normalized_text": "-0.0060",
  "numeric_value": -0.006,
  "sign": "-",
  "decimal_digits": 4,
  "bbox": [120, 340, 168, 361],
  "ocr_confidence": 0.71,
  "visual_candidates": ["-.0060", ".0060"],
  "visual_confidence": 0.84,
  "final_status": "needs_visual_review"
}
```

`raw_ocr` est append-only. Les champs critiques comprennent notamment prix, valeur théorique,
delta, gamma, theta, vega, volatilité implicite, débit/crédit, gain/perte maximum, break-even,
quantités et multiplicateur.

## 11. Tableaux

Pour chaque tableau, conserver :

- titre et numéro ;
- en-têtes simples et multi-niveaux ;
- ordre des colonnes et des lignes ;
- cellules fusionnées ;
- notes et unités ;
- page de début et éventuelles continuations ;
- bbox de chaque cellule ;
- OCR brut et valeur normalisée ;
- contrôles arithmétiques disponibles.

Un déplacement de colonne potentiel bloque le tableau entier pour usage quantitatif. Le rendu
Markdown ne doit jamais donner une impression de certitude supérieure au sidecar.

## 12. Formules

Chaque formule produit : OCR brut, LaTeX candidat, lecture textuelle, carte des symboles, crop,
ambiguïtés et statut. Une formule ne peut être corrigée parce qu'une autre formulation « paraît
mathématiquement logique ». Les contrôles peuvent signaler une contradiction, jamais réécrire la
source sans trace.

## 13. Figures et graphiques

Trois états sont séparés :

- `figure_extracted` : image et métadonnées disponibles ;
- `graph_described` : axes, légende et forme qualitative décrits ;
- `data_digitized` : points numériques calibrés et validés.

Une courbe non calibrable reste `image_only`. Gemini ou Codex ne doivent pas inventer des points à
partir d'une forme graphique.

## 14. Pagination et traçabilité

Conserver séparément :

```json
{
  "document_page_id": "sha256prefix:p000132",
  "pdf_page_index": 131,
  "pdf_page_number": 132,
  "printed_page_raw": "121",
  "printed_page_normalized": 121,
  "printed_page_confidence": 0.96,
  "chapter": "7",
  "section": "Position Greeks",
  "element_number": "7-2"
}
```

Toute interface et toute demande doivent préciser `PDF` ou `imprimée` lorsqu'une ambiguïté existe.

## 15. Confiance et statuts

Il n'existe pas de score moyen global. Conserver séparément : texte, layout, structure de tableau,
numérique, formule, pagination, accord visuel et validation métier.

Statuts autorisés :

- `machine_verified`
- `machine_verified_with_visual_check`
- `machine_reviewed`
- `needs_visual_review`
- `human_verified`
- `human_review_required`
- `blocked`
- `unextractable`
- `image_only`

Règles bloquantes initiales :

```python
if sign_disagreement or decimal_disagreement or column_shift_risk:
    status = "blocked"
if arithmetic_check_failed:
    status = "blocked"
if formula_structure_ambiguous:
    status = "needs_visual_review"
if gemini_failed:
    trigger_codex_fallback()
if codex_failed_or_remains_ambiguous:
    status = "human_review_required"
```

## 16. Contrôles déterministes

Les contrôles doivent être activables par type d'élément :

- syntaxe numérique, signe, séparateur et précision ;
- nombre et alignement des colonnes ;
- totaux, produits et sous-totaux visibles ;
- équations et identités explicitement présentes ;
- cohérence prix/payoff lorsque la source fournit les paramètres ;
- plages plausibles des Greeks uniquement comme alerte, jamais comme correction ;
- répétition d'en-têtes sur tableaux continués ;
- correspondance page/caption/figure.

## 17. Reprise, cache et idempotence

Une exécution interrompue doit reprendre sans retraiter les éléments inchangés. La clé de cache
inclut : SHA-256 du PDF, version pipeline, page, bbox, rotation, DPI, type d'élément, version OCR,
version prompt et version schéma.

Toute modification d'un de ces champs invalide la revue correspondante. Les écritures utilisent un
dossier temporaire puis un renommage atomique. Le rapport final liste les éléments réutilisés et
retraités.

## 18. Sécurité, confidentialité et coût

- clé API uniquement dans l'environnement local ;
- logs expurgés des secrets et chemins personnels ;
- paquets API minimaux et ciblés ;
- quotas, retry borné, backoff et limite de coût par run ;
- aucun upload du PDF complet par défaut ;
- conservation locale configurable des médias et réponses ;
- aucune preuve lourde versionnée dans Git.

## 19. Golden set et tests

Le golden set doit couvrir au minimum : texte natif, scan propre, skew, faible contraste, tableau
tourné, en-têtes multi-niveaux, décimales signées, fractions, formules, payoff diagram, graphique
multi-séries, annotations externes, pagination divergente, tableau continué, caption sur page
précédente, panne Gemini, JSON invalide, désaccord OCR/visuel et média Codex indisponible.

Les tests détaillés sont dans `../validation/pdf_transcription_v2_tests.md`.

## 20. Rapport final

Chaque run produit : livres et pages traités, éléments détectés par type, appels Gemini, fallbacks
Codex, éléments validés, bloqués ou à revoir, erreurs, coûts/latences, versions, chemins Markdown,
sidecars et file de revue.

## 21. Limites de portée

Cette V2 ne recommande aucune structure optionnelle, ne promeut aucune règle de recherche, ne
consomme aucune donnée broker live et n'envoie aucun ordre. Elle prépare un corpus fiable pour les
étapes de recherche, de validation et, plus tard, d'implémentation séparée.
