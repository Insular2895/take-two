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
| `07_transcription_pdf_technique_v2.md` | Contrat fiable PDF → JSON/Markdown/preuves avec Gemini et fallback Codex |
| `08_plan_implementation_transcription_v2.md` | Phases, gates et hors-périmètre de l'implémentation V2 |

Documents transverses hors `docs/` à lire aussi :

| Fichier | Contenu |
|---|---|
| `../tool_usage.md` | Rôle exact de Gemini, Codex, IBKR et des repos open source |
| `../evidence/README.md` | Dossiers de preuve par décision |
| `../references/source_weighting.md` | Hiérarchie de confiance des sources |
| `../schemas/README.md` | Contrats JSON du pipeline V2 |
| `../prompts/pdf_visual_verifier_gemini_v2.md` | Prompt strict du lecteur visuel Gemini |
| `../validation/pdf_transcription_v2_tests.md` | Golden set et tests de non-régression |

## Format attendu
Markdown pur, sections numérotées, aucun code métier. Le pseudo-code descriptif est autorisé
uniquement pour lever les ambiguïtés.

## Conventions
Voir `/CONVENTIONS.md`. Tout nouveau document méthodologique se place ici avec un préfixe numérique.

## Dépendances
- `rules/FORMAT_REGLE.md` (format officiel cité partout)
- `prompts/` (les prompts référencés par la méthodologie)
- `templates/` (modèles utilisés par le pipeline)
