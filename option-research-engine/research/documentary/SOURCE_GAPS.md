# Sources et pages encore nécessaires

Date : 2026-07-06

Statut : `to_review`

## Réponse courte

À ce stade, aucune nouvelle capture n'est nécessaire pour McMillan, Natenberg, Passarelli ou
Grinold/Kahn. Les PDF locaux et les captures déjà reçues suffisent pour les sections prioritaires.

Un statut Transcript `needs_review` ne signifie pas automatiquement que la page est illisible. Il
peut signaler une sortie Gemini mal formée, une citation trop courte ou une interprétation à
contrôler. Les pages sont rendues localement avant de solliciter une nouvelle capture.

## Source réellement manquante

### Annie Duke — *Thinking in Bets*

Le fichier disponible n'est pas le livre : il s'agit de notes secondaires de `15` pages.

À fournir seulement si cette source doit faire partie du corpus primaire :

- le PDF complet du livre ;
- idéalement une édition dont la page de copyright et la table des matières sont visibles.

Sans ce fichier, les notes restent `secondary_notes` et ne peuvent valider aucune citation attribuée
au livre.

## Source optionnelle, non bloquante

### Mauboussin et Rappaport — *Expectations Investing*

Le corpus contient l'édition originale de `2001`, complète et exploitable. Si le projet doit refléter
la méthodologie révisée, fournir l'édition `2021`. Ce n'est pas une panne d'extraction : c'est une
question de version.

### Repositories open source candidats

Trois repositories ont été ajoutés comme candidats de benchmark, mais ne sont pas encore validés
comme dépendances :

- OpTrade — `research/benchmarks/optrade.md`
- GraphVega — `research/benchmarks/graphvega.md`
- Keeks — `research/benchmarks/keeks.md`

Avant usage opérationnel, vérifier pour chacun :

1. URL exacte, licence et compatibilité avec le projet ;
2. activité réelle de maintenance, tests, issues et dépendances ;
3. conventions d'unités, définitions de Greeks / volatilité / P&L ;
4. reproductibilité des exemples ;
5. valeur objective par rapport à notre architecture.

## Pages déjà résolues localement

- McMillan, chapitre 25 LEAPS, pages imprimées `367–389` : extraction et revue ciblée effectuées.
- McMillan, tableau 25-2, page imprimée `384` : contrôle visuel effectué localement.
- Grinold/Kahn, chapitres 3, 5, 6 et 14–16 : équations et tableaux prioritaires lisibles après rendu.
- Natenberg, chapitres 4, 5, 6, 8, 9 et 13 : captures reçues et fiches documentaires créées.
- Passarelli, chapitre 13 et chapitre 14 : gamma scalping, P&L gamma/theta et configurations IV/RV
  documentés.

## Règle pour les prochaines demandes

Une capture utilisateur ne sera demandée que si les trois conditions suivantes sont réunies :

1. la page contient une formule, un tableau ou une figure nécessaire au modèle ;
2. le texte extrait et le rendu local ne permettent pas une lecture fiable ;
3. aucune autre édition locale ne permet de lever l'ambiguïté.

La demande précisera alors : livre, chapitre, page PDF, page imprimée si différente, numéro de
figure ou tableau, et champ exact à lire.
