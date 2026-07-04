# B-VINCE-1992 — The Mathematics of Money Management

## Auteur
Ralph Vince

## Année
1992

## Catégorie
MM (principale), PROBA

## Objectif
Fournir les fondations mathématiques du sizing : optimal f, fractions fixes, impact du drawdown,
lien entre distribution des résultats et taille de position.

## Niveau de confiance
MM : 4. Référence historique du position sizing ; l'optimal f exige des garde-fous (sur-agressif).

## Pourquoi ce livre est important
Le moteur doit optimiser la répartition du budget entre structures : Vince fournit le cadre formel
reliant distribution des gains simulée (Monte Carlo) et fraction optimale du capital.

## Modules concernés
sizing, money_management, scoring (composante risque), simulation.

## Informations recherchées (très précisément)
- Optimal f : définition, calcul, données nécessaires, et TOUS les avertissements de l'auteur.
- Relation drawdown ↔ fraction investie → règles de plafonnement.
- Traitement des distributions non normales → conditions de validité.
- Méthodes de combinaison de positions simultanées.

## Prompt Gemini spécifique
Tu extrais des règles de « The Mathematics of Money Management » (Vince). Base : prompt MM.
Spécialisations : (1) Chaque formule doit devenir une règle de calcul (Variables nécessaires =
distribution simulée des P&L). (2) Chaque avertissement de l'auteur sur l'agressivité de
l'optimal f devient une règle de garde-fou (plafond, fractionnement). (3) Les exemples numériques
du livre alimentent le champ Exemple tels quels. Sortie : format officiel, chapitre + page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format officiel exclusivement.

## Journal de traitement
- (vide)
