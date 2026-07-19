# Plan d'implémentation — Pipeline de transcription V2

Statut : `draft_to_validate`  
Référence : `07_transcription_pdf_technique_v2.md`

## 1. But

Transformer la spécification V2 en un outil local relançable, observable et auditable, sans
mélanger transcription documentaire et logique de trading.

## 2. Séquence de livraison

### P0 — hygiène et contrats

- protéger PDF, secrets, médias et sorties lourdes avec `.gitignore` ;
- figer les statuts et schémas JSON ;
- définir `document_id`, `run_id`, `element_id` et la politique de version ;
- créer les fixtures minimales du golden set ;
- définir les sorties versionnables et locales uniquement.

Critère de sortie : schémas valides, conventions documentées, aucune source protégée dans Git.

### P1 — inspection locale et paquets de preuve

- implémenter `pdf_transcriber.inspect` ;
- rendre page/crop à DPI contrôlé ;
- détecter/appliquer la rotation sans altérer la source ;
- ajouter contexte précédent/suivant en mode `auto` ;
- produire `metadata.json` et retourner les chemins ;
- garantir qu'aucun Markdown n'est modifié.

Critère de sortie : une page connue produit un paquet complet et reproductible.

### P2 — extraction locale

- manifeste et hashing ;
- texte natif et OCR conditionnel ;
- segmentation layout ;
- extracteurs texte/table/formule/figure ;
- pagination PDF/imprimée ;
- sidecar canonique ;
- contrôles déterministes ;
- cache et reprise.

Critère de sortie : le corpus test est transcrit sans appel distant et toutes les ambiguïtés sont
signalées.

### P3 — intégration Gemini

- client API avec timeout, backoff et budget ;
- envoi du paquet minimal ;
- prompt versionné ;
- structured output conforme au schéma ;
- une seule réparation de JSON ;
- comparaison champ par champ avec OCR et sidecar ;
- archivage de la réponse brute.

Critère de sortie : un tableau connu est vérifié ; une panne et un JSON invalide déclenchent le
fallback attendu.

### P4 — fallback Codex et file de revue

- déclencher automatiquement l'inspection locale ;
- vérifier la disponibilité média ;
- écrire `codex_review.json` sans modifier la transcription ;
- produire la file `human_review_required` ;
- permettre une résolution humaine avec auteur, date, motif et preuve.

Critère de sortie : aucune ambiguïté critique n'est promue automatiquement.

### P5 — golden set et qualité

- annoter les cas G01 à G19 ;
- tester signes, décimales, fractions, colonnes, rotations, formules et pagination ;
- mesurer erreurs dangereuses non signalées, faux blocages, couverture, latence et coût ;
- définir des seuils de non-régression.

Critère de sortie : zéro erreur quantitative dangereuse acceptée sur le golden set.

### P6 — orchestration complète

- commande unique `transcribe` ;
- détection de tous les PDF fournis ;
- exécution page par page avec reprise ;
- appels visuels automatiques ;
- génération Markdown/JSON/preuves/rapport ;
- journal structuré et résumé final.

Critère de sortie : une demande « lance la transcription complète » suffit hors blocage réel.

### P7 — raccord au pack de recherche

- importer uniquement les éléments `human_verified` ou suffisamment validés selon leur criticité ;
- conserver le lien vers preuve, source, page et version ;
- créer les règles en statut `EXTRACTED`, jamais directement `VALIDATED` ;
- empêcher une règle issue d'un élément `blocked` ou `image_only` d'alimenter le moteur futur.

Critère de sortie : traçabilité bidirectionnelle règle -> élément -> page -> PDF local.

## 3. Arborescence cible suggérée

```text
pdf_transcriber/
  cli.py
  ingest.py
  render.py
  layout.py
  ocr.py
  extractors/
    text.py
    tables.py
    formulas.py
    figures.py
  validation/
    numeric.py
    arithmetic.py
    options_domain.py
  visual/
    gemini.py
    codex_fallback.py
  review.py
  report.py
tests/
  fixtures/golden/
  test_inspect.py
  test_schemas.py
  test_visual_fallback.py
```

Cette arborescence reste indicative jusqu'à l'audit du dépôt `/Users/insular/transcripts`, qui doit
être réutilisé lorsqu'il fournit déjà une fonction équivalente et testée.

## 4. Décisions à valider avant code complet

1. runtime Python et gestionnaire de dépendances ;
2. librairie de rendu PDF ;
3. moteurs OCR/layout/table/formule réellement retenus ;
4. modèle Gemini, structured output et budget par livre ;
5. politique locale de rétention des preuves ;
6. taille et licences du golden set ;
7. seuils de confiance après mesure, pas par intuition.

Ces points restent `draft_to_validate` : cette documentation n'est pas une décision d'architecture
finale.

## 5. Hors périmètre

- recommandation d'un trade ;
- scoring d'option live ;
- connexion IBKR et passage d'ordre ;
- activation automatique des règles extraites ;
- publication des livres ou captures longues ;
- correction éditoriale silencieuse des sources.
