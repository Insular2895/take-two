# Dossier humain de revue — commencer ici

> **STATUT : CODE READ-ONLY PRÉPARÉ HORS CONNEXION — VALIDATION IBKR/OPRA RÉELLE EN ATTENTE.**
>
> Ce dossier explique le système. Il n’autorise ni position, ni ordre, ni campagne paper.

## À quoi sert ce dossier ?

Il permet à une personne qui ne connaît pas le dépôt de répondre, dans cet ordre, à cinq
questions :

1. Que fait réellement le bot ?
2. Quelles données utilise-t-il et comment évite-t-il de les inventer ?
3. Comment transforme-t-il une chaîne options en décision de recherche ?
4. Où se trouvent les frontières IBKR, Cloudflare et paper trading ?
5. Qu’est-ce qui est codé, testé, observé réellement ou encore bloqué ?

## Le résumé en une minute

Le projet est un moteur de recherche sur les options TTWO. Il peut construire et comparer des
structures à risque borné, calculer leur économie, simuler plusieurs modèles, appliquer des vetoes
et produire un verdict explicable. Son résultat actuel reste `NO_POSITION_RECOMMENDED` et
`ENGINE_NOT_PROVEN_SUPERIOR`.

Le nouveau provider IBKR sait, côté code :

- ouvrir uniquement une session paper read-only locale ;
- vérifier les gates humains d’entitlement et de licence avant le premier appel réseau ;
- qualifier le sous-jacent et les contrats options ;
- découvrir les expirations, capturer spot, bid/ask, tailles, volume, open interest et Greeks ;
- préserver la provenance et les timestamps sans transformer une heure de réception en heure
  d’échange ;
- borner la chaîne, le pacing, les retries et le cache ;
- exposer des compteurs redacted de retry, pacing, cache expiré et absence de stale fallback ;
- demander une quote de marché BAG sans créer d’ordre ;
- comparer cette quote au synthétique des jambes ;
- normaliser hors ligne une observation what-if déjà obtenue, sans méthode d’ordre ;
- ajouter prospectivement décisions et réalisations shadow sous manifeste approuvé ;
- convertir le résultat vers le `MarketSnapshot` canonique du moteur.

Ce code n’a pas encore été validé sur une chaîne TTWO réelle. Une ancienne connexion IBKR Paper a
validé le handshake, le compte `DU` et un snapshot sans position TTWO, mais pas la nouvelle chaîne
complète, les quotes BAG, l’open interest, les Greeks ni les comportements de pacing réels.

## Ordre de lecture recommandé

1. [Résumé du produit](01_RESUME_PROJET.md)
2. [Carte du système](02_ARCHITECTURE_ET_FLUX.md)
3. [Décisions et raisons](03_DECISIONS_ET_COMPROMIS.md)
4. [Invariants de sécurité](04_INVARIANTS_SECURITE.md)
5. [Données et provenance](05_DONNEES_ET_NORMALISATION.md)
6. [Moteur quantitatif](06_MOTEUR_QUANTITATIF.md)
7. [Intégration IBKR](07_INTEGRATION_IBKR.md)
8. [Cloudflare et Oracle](08_CLOUDFLARE_ORACLE.md)
9. [Validation et niveau de preuve](09_VALIDATION_ET_PREUVES.md)
10. [Exploitation et continuité](10_OPERATIONS_ET_CONTINUITE.md)
11. [Commandes et branchement futur](11_RUNBOOK.md)
12. [Ce qui reste ouvert](12_ELEMENTS_A_VALIDER.md)
13. [Glossaire](13_GLOSSAIRE.md)
14. [Traçabilité](14_TRACABILITE.md)
15. [Protocole de branchement IBKR](15_PROTOCOLE_BRANCHEMENT_IBKR.md)
16. [Contrôle de campagne shadow](16_CAMPAGNE_SHADOW.md)
17. [What-if hors ligne et preuve de résilience](17_WHAT_IF_ET_RESILIENCE.md)

## Règle de lecture des statuts

| Statut | Signification |
|---|---|
| `CODÉ` | Le comportement existe dans le dépôt. |
| `TESTÉ_OFFLINE` | Des tests déterministes prouvent le contrat logiciel sans broker. |
| `OBSERVÉ_RÉELLEMENT` | Le comportement a été vu sur un système externe identifié. |
| `PARTIEL` | Une partie seulement du chemin réel a été observée. |
| `HUMAIN_REQUIS` | Le dépôt ne peut pas décider à la place du titulaire du compte. |
| `BLOQUÉ` | La capacité reste indisponible tant que les preuves exigées manquent. |

`CODÉ` ne signifie jamais `OBSERVÉ_RÉELLEMENT`. `TESTÉ_OFFLINE` ne signifie jamais qu’une
stratégie est rentable. Une connexion réussie ne signifie jamais que l’entitlement OPRA, la
licence ou une campagne paper sont validés.

## Red-team : toute réponse « oui » bloque la promotion

- Une donnée absente devient-elle silencieusement zéro ?
- Une quote reçue localement est-elle présentée comme horodatée par l’exchange ?
- Une chaîne trop grande est-elle tronquée sans signalement ?
- Un retry read-only peut-il appeler une méthode d’ordre ?
- Une quote BAG peut-elle être déclarée confirmée sans convention de signe validée ?
- Une estimation de marge peut-elle être inventée en l’absence de réponse broker ?
- Un dataset synthétique peut-il promouvoir un candidat réel ?
- Un score peut-il contourner un hard gate ?
- Une connexion paper peut-elle accepter un compte non `DU` ?
- Le retour à la santé peut-il démarrer automatiquement le paper trading ?
