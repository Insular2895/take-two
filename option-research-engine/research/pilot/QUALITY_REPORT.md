# Rapport qualité du pilote PDF

Date : 2026-07-05

Statut : `pilot_passed_with_guards`

## Périmètre

Le pilote a testé trois chemins :

- extraction texte directe sur les 40 premières pages de McMillan ;
- OCR des 20 premières pages de Natenberg ;
- OCR des 20 premières pages de Passarelli.

Les PDF originaux sont restés inchangés. Les Markdown intégraux, sorties Gemini et fichiers OCR
restent dans le worktree local ignoré de Summarizer.

## Outil

Branche Summarizer : `codex/take-two-pdf-research`

Fonctions ajoutées :

- découpage sans casser les pages PDF ;
- manifeste par chunk ;
- reprise sans retraitement des chunks terminés ;
- statut `needs_review` pour une sortie mal formée ;
- vérification d'une preuve source courte contre la page PDF revendiquée ;
- création d'un véritable sous-PDF avant OCR d'un échantillon.

Baseline après modifications : 53 tests passants.

## Résultats

### McMillan

- PDF : 5e édition, copie texte, 1 069 pages.
- Pilote : pages PDF 1 à 40.
- Chunks : 2.
- Règles produites avec le prompt final : 4.
- Chunks validés automatiquement après normalisation des césures PDF : 2 sur 2.
- Revue manuelle :
  - 3 règles soutenues et correctement bornées ;
  - 1 règle `to_review`, car le texte décrit une possibilité de vente avant dividende et la sortie
    Gemini la transforme en prescription trop forte.
- Décision : `go_full_with_manual_review`.

### Natenberg

- PDF : 475 pages scannées et structurellement mal formées.
- Pilote : pages PDF 1 à 20.
- OCR : réussi après création d'un sous-PDF de travail.
- Règles produites : 1.
- Résultat documentaire : l'idée est bien présente, mais Gemini revendique `PDF_PAGE: 19` alors que
  sa preuve se trouve sous `# Page 20`.
- Le validateur déterministe marque le chunk `needs_review`.
- Décision : `go_full_with_citation_guard`; aucune règle n'est promue sans validation automatique
  puis revue manuelle.

### Passarelli

- PDF : 357 pages scannées.
- Pilote : pages PDF 1 à 20.
- OCR : réussi.
- Règles produites avec le prompt final : 0.
- Sortie : `AUCUNE_REGLE_EXPLOITABLE`.
- Interprétation : résultat correct pour un bloc principalement composé de préface, introduction
  et présentation générale ; le pipeline n'a pas forcé une règle de Greeks.
- Décision : `go_full`.

## Usage Gemini du pilote et des itérations

- Requêtes : 9.
- Réussies : 9.
- Échouées : 0.
- Tokens d'entrée : 74 897.
- Tokens de sortie : 11 316.
- Coût : non calculable avec la configuration tarifaire locale actuelle.

Ces chiffres incluent les relances de calibration des prompts.

## Incidents et corrections

### PDF Natenberg invalide après OCR

Cause racine :

- le PDF source contient des flux image mal formés ;
- avec `--max-pages`, OCRmyPDF conservait les pages non sélectionnées dans le fichier final ;
- le contrôle final retrouvait donc les flux corrompus.

Correction :

- QPDF crée un vrai sous-PDF contenant uniquement la plage pilote ;
- OCRmyPDF traite ensuite l'intégralité de ce sous-PDF ;
- le résultat passe le contrôle QPDF sans erreur de syntaxe ou d'encodage.

### Citation Natenberg décalée

Cause :

- Gemini a utilisé le mauvais numéro malgré une consigne de pagination explicite.

Correction :

- chaque règle contient désormais `## Preuve source` ;
- le logiciel vérifie que cette preuve apparaît dans la ou les pages PDF revendiquées ;
- une incohérence devient automatiquement `needs_review`.

### Faux négatif sur McMillan

Cause :

- le PDF coupe certains mots avec un caractère soft-hyphen suivi d'un retour à la ligne.

Correction :

- le validateur normalise cette césure avant comparaison ;
- la preuve reste exacte sans rendre la comparaison permissive sur les nombres.

## Critères de sortie du pilote

- Pagination préservée : validé.
- Aucune règle promue sans page : validé.
- Aucune citation fausse acceptée silencieusement : validé.
- Reprise par chunk : validé par tests.
- OCR Natenberg et Passarelli : validé sur échantillon.
- Traitement intégral : à exécuter.
- Validation quantitative ou rentabilité : hors périmètre et non réalisée.

## Décision

Le pipeline peut passer au traitement intégral des sources approuvées. Les sorties restent de la
recherche documentaire. Elles ne sont ni des recommandations de trading, ni des règles actives, ni
une autorisation de créer ou lancer un script IBKR.
