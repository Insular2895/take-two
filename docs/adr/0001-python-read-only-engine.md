# ADR 0001 — Python pour le moteur read-only V1

Date : 2026-07-18

Statut : `accepted_for_read_only_v1`

## Contexte

Le dépôt contenait un corpus documentaire sans stack applicatif. La V1 devait être typée,
reproductible, testable hors ligne, indépendante d'IBKR et petite à installer.

## Décision

Utiliser Python 3.11+, package `src/`, Pydantic v2, Typer, pytest, Ruff et mypy. Les calculs V1
Black-Scholes, payoffs et Monte-Carlo simple utilisent la bibliothèque standard ; aucune grosse
dépendance numérique n'est nécessaire à cette portée.

Les sorties locales JSON/Markdown forment le stockage reproductible V1. Un stockage SQLite,
DuckDB ou Parquet ne sera ajouté que si l'historisation de chaînes ou le backtest V2 le justifie.

## Conséquences

- contrats stricts et schéma JSON générable ;
- CLI installable et tests offline rapides ;
- cœur métier sans dépendance broker ;
- modèle américain, calibration et surfaces avancées volontairement hors V1 ;
- toute future librairie de pricing devra être licenciée, comparée aux tests indépendants et
  isolée derrière une interface.
