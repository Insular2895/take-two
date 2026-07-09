# tool_usage.md — Rôle exact des outils

## Objectif

Ce fichier empêche la confusion entre extraction, recherche, développement, validation et exécution.
Aucun outil ne doit être traité comme une source de vérité universelle.

## Gemini

Usage autorisé :

- extraction de livres, PDF ou Markdown chapitre par chapitre ;
- transformation de passages en règles candidates ;
- repérage de contradictions, tableaux, formules et exemples ;
- production de brouillons `EXTRACTED`.

Limites :

- Gemini ne valide pas une règle ;
- Gemini peut mal lire une page, une formule, un tableau ou une pagination OCR ;
- toute sortie Gemini reste `EXTRACTED` tant qu'elle n'est pas vérifiée par source, revue visuelle,
  simulation ou validation humaine selon le risque.

## Codex

Usage autorisé :

- structuration du repository ;
- recherche, consolidation, déduplication et documentation ;
- écriture de code seulement après validation de la phase de recherche ;
- génération de tests, simulateurs, collecteurs read-only et outils d'audit ;
- préparation de propositions traçables avec règles, sources, simulations et limites.

Limites :

- Codex ne transforme pas une idée en décision d'exécution sans validation explicite ;
- Codex ne doit pas coder de règle arbitraire ;
- Codex ne doit pas faire de recommandation de trade live sans données broker/live et validation
  humaine.

## IBKR

Usage autorisé :

- collecte read-only : chaîne d'options, contract details, bid/ask, Greeks, IV, open interest si
  disponible, marge et commissions ;
- order preview / estimation pré-trade ;
- paper trading pour vérifier exécution, logs, latence, slippage et P&L attribution ;
- préparation d'ordre après validation humaine.

Limites :

- aucun ordre réel automatique ;
- aucun envoi sans validation humaine explicite ;
- pas de hard-code du multiplicateur `100` : utiliser les contract details ;
- toute donnée de marché doit être horodatée et marquée stale si elle dépasse son délai de fraîcheur.

## Repositories open source

Usage autorisé :

- inspiration d'architecture ;
- benchmark de méthodes numériques, UI, pipeline de données ou sizing ;
- comparaison de pratiques ;
- source de tests d'idées.

Limites :

- un repo GitHub n'est pas une source de vérité ;
- aucune règle de trading ne devient `VALIDATED` parce qu'un repo l'implémente ;
- toute dépendance doit être auditée : licence, maintenance, sécurité, exactitude, tests.

## Transcript / PDF research tooling

Usage autorisé :

- convertir les PDF ou sources longues en Markdown exploitable ;
- conserver la provenance : livre, chapitre, page PDF, page imprimée si disponible ;
- isoler les tableaux/formules à revoir visuellement ;
- alimenter les prompts Gemini.

Limites :

- les PDF originaux ne sont pas commités ;
- les OCR et conversions peuvent déformer chiffres, signes, colonnes ou formules ;
- les tableaux et formules utilisés pour le quantitatif doivent avoir une revue visuelle ou une
  vérification numérique indépendante.
