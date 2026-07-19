# Schémas JSON — transcription PDF V2

Ces schémas sont les contrats de données du pipeline documentaire.

| Fichier | Rôle |
|---|---|
| `gemini_visual_review.schema.json` | Réponse structurée obligatoire du vérificateur visuel |
| `pdf_element_sidecar.schema.json` | Représentation canonique d'un élément extrait |

Règles :

- toute version incompatible nécessite un nouveau numéro de version ;
- une réponse Gemini invalide n'est jamais interprétée comme du texte libre ;
- le sidecar conserve toujours les lectures brutes et normalisées ;
- le Markdown ne remplace jamais le sidecar.

