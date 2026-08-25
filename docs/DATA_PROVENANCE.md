# Provenance et point-in-time

L’observation unifiée contient série, temps d’observation, temps de récupération,
cutoff, valeur, unité, fournisseur, source, domaine, qualité, fraîcheur, validité
point-in-time, hash brut, droits d’usage et métadonnées.

## Règles fail-closed

- timestamp futur ou post-cutoff : exclusion ;
- timestamp de quote absent : blocage à la validation d’entrée ;
- unité incohérente : rejet de la série concernée ;
- contenu dupliqué : signalement et déduplication ;
- source absente du registre : qualité inconnue et diagnostic ;
- donnée périmée : `stale`, puis blocage si la série requise dépasse sa politique ;
- panne d’un connecteur : état `unavailable`, `failed` ou `partial`, jamais donnée
  inventée.

Les états de connecteur sont `not_configured`, `unavailable`, `failed`, `partial` et
`ready`. Les messages d’erreur réseau sont nettoyés des URL et clés potentielles.

La suite d’erreurs reproductible est dans
`fixtures/v11/observation_error_cases.json`. Le schéma canonique est
`schemas/observation.schema.json`.

Les droits de redistribution ne sont jamais inférés de l’accès technique. Ils doivent
être documentés et approuvés séparément.
