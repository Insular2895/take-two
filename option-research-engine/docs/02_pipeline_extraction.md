# Pipeline d'extraction : PDF → Markdown → Règles

> Ce document décrit le flux de recherche historique. Pour les PDF techniques contenant tableaux,
> formules, graphiques ou valeurs quantitatives, la spécification normative est désormais
> `07_transcription_pdf_technique_v2.md`. Aucun élément critique ne peut être promu sans sidecar JSON,
> preuve visuelle et statut conforme à cette V2.

## Étape 1 — Conversion PDF → Markdown

- Un fichier Markdown par livre, découpé par chapitre : `books/markdown/<book_id>/ch<NN>.md`
  (dossier créé au moment du traitement ; les PDF sources ne sont jamais commités pour raisons de droits).
- La pagination d'origine est conservée sous forme de marqueurs `[p. 123]` afin de garantir la
  traçabilité Auteur/Livre/Chapitre/Page exigée par le format officiel des règles.
- Tableaux et formules sont convertis en JSON canonique puis rendus en Markdown ; les figures sont
  extraites et décrites sans numérisation quantitative implicite.
- Les pages PDF et imprimées sont conservées séparément.
- Toute ambiguïté de signe, décimale, colonne ou formule bloque l'usage quantitatif.

## Étape 2 — Passage Gemini

- Entrée règle : un chapitre Markdown validé + ses sidecars et preuves, puis le prompt spécifique du
  livre.
- Sortie : **uniquement** des blocs au format officiel de `rules/FORMAT_REGLE.md`.
- Toute sortie qui ressemble à un résumé est rejetée et le passage est relancé.
- Chaque bloc doit citer chapitre + page (via les marqueurs `[p. N]`).
- Gemini peut extraire ou vérifier visuellement, mais ne valide jamais seul une règle.

## Étape 3 — Contrôle qualité automatique

Une règle est rejetée si :
- un champ obligatoire du format officiel est vide ;
- la source (chapitre/page) est absente ;
- la condition n'est pas testable (pas de variable identifiable) ;
- l'action n'est pas exécutable par un moteur (verbe flou : « faire attention à… »).

## Étape 4 — Dépôt

- Règles brutes : `rules/<categorie>/` (une règle par fichier, nommée par son identifiant).
- Les règles consolidées (après déduplication/pondération) sont référencées dans `knowledge_base/`.

## Étape 5 — Journal de traitement

Chaque livre traité reçoit une entrée de journal dans sa fiche : date, version du prompt,
nombre de règles extraites / rejetées, anomalies rencontrées.
