# Pipeline d'extraction : PDF → Markdown → Règles

## Étape 1 — Conversion PDF → Markdown

- Un fichier Markdown par livre, découpé par chapitre : `books/markdown/<book_id>/ch<NN>.md`
  (dossier créé au moment du traitement ; les PDF sources ne sont jamais commités pour raisons de droits).
- La pagination d'origine est conservée sous forme de marqueurs `[p. 123]` afin de garantir la
  traçabilité Auteur/Livre/Chapitre/Page exigée par le format officiel des règles.
- Tableaux et formules sont convertis en Markdown ; les figures sont décrites en texte.

## Étape 2 — Passage Gemini

- Entrée : un chapitre Markdown + le prompt spécifique du livre (issu de sa fiche).
- Sortie : **uniquement** des blocs au format officiel de `rules/FORMAT_REGLE.md`.
- Toute sortie qui ressemble à un résumé est rejetée et le passage est relancé.
- Chaque bloc doit citer chapitre + page (via les marqueurs `[p. N]`).

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
