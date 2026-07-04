# Méthodologie de recherche

## 1. Philosophie

Les livres ne sont **pas** destinés à être résumés. Ils sont la source principale de connaissances
du moteur de décision. L'objectif n'est jamais de comprendre un livre dans son ensemble : l'objectif
est de **transformer son contenu en règles exploitables** par le moteur d'optimisation.

Chaque livre possède une expertise différente. La méthode d'extraction s'adapte donc
automatiquement au domaine du livre.

## 2. Cycle de traitement d'un livre

1. **Identification** — type de livre, domaine d'expertise, catégorie officielle (voir `CONVENTIONS.md`).
2. **Fiche** — création de la fiche livre dans `books/fiches/` à partir de `templates/fiche_livre.md`.
3. **Conversion** — le PDF est converti en Markdown (voir `02_pipeline_extraction.md`).
4. **Sélection du prompt** — on part du prompt de catégorie (`prompts/categories/`), puis on le
   spécialise pour le livre (le prompt final, propre au livre, vit dans sa fiche). **Un prompt
   générique n'est jamais utilisé tel quel.**
5. **Extraction par Gemini** — Gemini lit le Markdown chapitre par chapitre et produit uniquement
   des règles au format officiel (`rules/FORMAT_REGLE.md`). Aucun résumé.
6. **Normalisation** — chaque règle reçoit un identifiant `R-<CAT>-<NNN>` et est déposée dans `rules/`.
7. **Déduplication et contradictions** — voir `03_contradictions_et_doublons.md`.
8. **Pondération** — voir `04_ponderation_des_regles.md`.
9. **Intégration** — la règle consolidée entre dans `knowledge_base/`. Les règles y sont
   **cumulatives** : un nouveau livre enrichit la base, il ne remplace jamais l'existant.
10. **Validation** — la règle est marquée « à valider par simulation » tant que `validation/`
    ne contient pas de protocole exécuté la confirmant.

## 3. Ce que Gemini doit extraire (et rien d'autre)

Règles, méthodes, seuils numériques, exceptions, exemples chiffrés, erreurs à éviter,
critères de décision (achat, vente, gestion, rolling, sizing). Toute information ne permettant
pas d'améliorer directement le moteur est ignorée.

## 4. Question unique posée à chaque livre

> « Comment ce livre améliore-t-il objectivement le moteur de décision ? »

Modules cibles : sélection des options, choix des strikes, choix des échéances, sizing,
gestion des gains, gestion des pertes, règles de vente, trailing stops, rolling,
simulations, scoring, robustesse.

## 5. Intégration continue des connaissances

À chaque nouveau livre traité, le pipeline détecte automatiquement :
- les **convergences** (plusieurs auteurs → confiance renforcée, cf. pondération) ;
- les **contradictions** (conservées et arbitrées, jamais écrasées silencieusement) ;
- les **nouvelles règles** (ajoutées avec statut `EXTRAITE`).
