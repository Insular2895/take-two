# REPO-GS-QUANT — GS Quant (Goldman Sachs)

Nature : toolkit Python d'analytics financiers. Licence : Apache 2.0 (services GS soumis à accès).
Maturité : élevée. Étude ciblée : pricing, dérivés, risk management, modèles financiers,
architecture, abstractions, calculs, analytics, scénarios, stress tests.

## 1. Ce que ce projet fait mieux que nous
Abstractions institutionnelles propres : objets instrument/portefeuille, mesures de risque
normalisées, framework de scénarios et de stress tests de qualité professionnelle.

## 2. Ce qu'il ne fait pas
Pas de moteur de décision ni de sélection de stratégie ; une partie de la valeur dépend des
services Goldman (non réutilisable) ; aucune base de règles issue de littérature.

## 3. Ce que nous pouvons réutiliser
Le design des abstractions : séparation instrument / mesure / scénario, API de stress tests
(inspiration directe pour `simulations/` et `risk/`), conventions de définition des chocs.

## 4. Ce que nous devons améliorer
Autonomie complète (aucune dépendance à un service propriétaire) ; scénarios pilotés par nos
règles et nos hypothèses documentées plutôt que par des presets.

## 5. Pourquoi notre architecture sera différente
GS Quant outille des professionnels qui décident ; notre moteur DÉCIDE (puis explique) sous
contrainte de règles sourcées, avec validation humaine finale.
