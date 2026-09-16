# Phase M — checkpoint provider IBKR read-only hors ligne

Date : 16 septembre 2026  
Statut : `OFFLINE_IMPLEMENTATION_COMPLETE_LIVE_VALIDATION_PENDING`

## Résultat

Le dépôt dispose maintenant d'un adaptateur de données de marché IBKR limité au compte paper et
au loopback. Il couvre la qualification TTWO, la découverte/qualification des contrats options,
le spot, les snapshots d'options, les tailles, le volume, l'open interest, les Greeks, la
normalisation, la provenance, les hashes, le cache, le retry/pacing et les quotes BAG.

Une commande CLI explicite produit le snapshot strict et, en option, sa conversion vers le
`MarketSnapshot` canonique. Sans `--connect-read-only`, elle s'arrête avant import dynamique du
client IBKR et avant toute connexion.

## Frontière de sécurité

- mode `paper` obligatoire ;
- hôte loopback obligatoire ;
- compte `DU` obligatoire ;
- allowlist `TTWO` ;
- entitlement et licence requis avant tout appel transport ;
- aucun type `Order`, aucun submit/modify/cancel/exercise ;
- aucune donnée manquante transformée en zéro ;
- aucun snapshot périmé utilisé en fallback ;
- exécution et campagne paper inchangées et désactivées.

## Preuves de ce checkpoint

- tests unitaires/fake transport pour les gates, la normalisation, la complétude, le cache, les
  retries, la conversion moteur, BAG/synthétique et le désarmement CLI ;
- typage strict et lint du nouveau code ;
- schémas JSON générés pour `LiveComboQuote` et `BrokerWhatIfEvidence` ;
- scan statique du transport officiel interdisant les primitives d'ordre.

Validation locale après intégration : 409 tests Python, Ruff, mypy strict sur 197 fichiers source,
36 schémas JSON, artefacts offline, registre de recherche, audits Phase 10/11 et gate sécurité ;
13 tests et Ruff pour le bridge ; 63 tests, typecheck et safety scan pour le Worker.

## Ce qui n'est pas prouvé

- installation et comportement runtime de l'API officielle `ibapi` dans l'environnement final ;
- nouvelle capture de chaîne TTWO réelle ;
- entitlement OPRA, licence, stockage et redistribution ;
- sémantique exacte des timestamps, disponibilité OI/Greeks et pacing réels ;
- convention de signe BAG ;
- commissions/marge what-if ;
- télémétrie complète Oracle vers Cloudflare avec une position TTWO ;
- shadow, paper, rentabilité ou supériorité du moteur.

Le handshake paper observé le 25 août 2026 reste une preuve utile mais distincte : il valide une
connexion de base et un compte `DU`, pas ce nouveau chemin de chaîne.

## Fichiers principaux

- `src/take_two_options/opra/ibkr_provider.py` ;
- `src/take_two_options/opra/ibkr_official.py` ;
- `src/take_two_options/opra/contracts.py` ;
- `src/take_two_options/cli.py` ;
- `tests/test_ibkr_opra_provider.py` ;
- `docs_v2/_review/`.
