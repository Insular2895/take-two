# docs/ — Documentation transverse

## Rôle
Contient toute la documentation de méthodologie et de spécification qui ne relève ni d'un livre
précis, ni d'une catégorie de connaissance précise.

## Contenu
| Fichier | Contenu |
|---|---|
| `01_methodologie_recherche.md` | Comment les livres sont lus, convertis, exploités par Gemini |
| `02_pipeline_extraction.md` | Pipeline PDF → Markdown → Règles, étape par étape |
| `03_contradictions_et_doublons.md` | Détection des contradictions, suppression des doublons |
| `04_ponderation_des_regles.md` | Pondération des règles et des auteurs |
| `05_onboarding_codex.md` | Point d'entrée unique pour Codex |
| `06_moteur_maintenance.md` | Spécification documentaire du moteur de maintenance |

## Format attendu
Markdown pur, sections numérotées, aucun code métier. Le pseudo-code descriptif est autorisé
uniquement pour lever les ambiguïtés.

## Conventions
Voir `/CONVENTIONS.md`. Tout nouveau document méthodologique se place ici avec un préfixe numérique.

## Dépendances
- `rules/FORMAT_REGLE.md` (format officiel cité partout)
- `prompts/` (les prompts référencés par la méthodologie)
- `templates/` (modèles utilisés par le pipeline)
