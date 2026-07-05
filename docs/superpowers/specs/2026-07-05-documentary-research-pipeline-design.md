# Pipeline de recherche documentaire pour Take Two

Statut : design approuve en conversation, a relire avant implementation.

Date : 2026-07-05

## 1. Objectif

La premiere phase de Take Two est exclusivement un systeme de recherche documentaire.

Elle transforme un corpus local de livres financiers en connaissances structurees, tracables et
testables. Elle ne produit ni conseil de trading, ni recommandation d'achat, ni ordre IBKR, ni code
d'execution de strategie.

Le systeme doit repondre a cette question :

> Quelles regles exploitables, limites, contradictions et exigences de validation peut-on extraire
> de chaque source pour preparer un futur moteur d'analyse d'options ?

## 2. Principes non negociables

- Les PDF originaux restent inchanges dans leur emplacement actuel.
- Les PDF et leur transcription integrale ne sont jamais commites dans Git.
- Le repo `/Users/insular/transcripts` est reutilise pour la conversion PDF vers Markdown, l'OCR et
  les appels Gemini. Take Two ne recree pas un second convertisseur.
- Gemini extrait et structure ; il ne valide pas une affirmation.
- Toute regle conserve son auteur, son livre, son edition, son chapitre et sa page.
- Une information sans provenance exploitable est rejetee ou marquee `to_review`.
- Une contradiction n'est jamais ecrasee silencieusement.
- Une regle extraite reste inactive tant qu'elle n'a pas passe les controles prevus.
- Les connaissances de Maxi Brain servent de contexte et de controle croise, pas de preuve magique.

## 3. Corpus pilote

Le corpus contient neuf documents uniques.

### Sources principales pour les options

1. Lawrence G. McMillan, *Options as a Strategic Investment*, 5e edition.
2. Sheldon Natenberg, *Option Volatility and Pricing*.
3. Dan Passarelli, *Trading Option Greeks*.
4. Mark Douglas, *Trading in the Zone*.
5. Richard Grinold et Ronald Kahn, *Active Portfolio Management*, 2e edition.

### Sources complementaires pour la selection et la decision

6. Seth Klarman, *Margin of Safety*.
7. Michael Mauboussin et Alfred Rappaport, *Expectations Investing*, edition 2001.
8. Peter Lynch, *One Up On Wall Street*.
9. Annie Duke, notes secondaires de 15 pages sur *Thinking in Bets*.

Les deux fichiers Natenberg fournis contiennent les memes pages. Un seul exemplaire est traite.
Les notes Annie Duke recoivent le type `secondary_notes` et ne peuvent pas soutenir seules une
regle active.

## 4. Architecture

Le systeme est divise en six unites independantes.

### 4.1 Inventaire

Entree :

- chemins locaux fournis ;
- fiches bibliographiques de `option-research-engine/books/fiches/`.

Sortie :

- manifeste du corpus ;
- empreinte SHA-256 ;
- nombre de pages ;
- edition detectee ;
- statut de couche texte ;
- besoin d'OCR ;
- doublons ;
- anomalies PDF.

### 4.2 Preparation documentaire

Le pipeline choisit par livre :

- extraction texte directe si la couche texte est suffisante ;
- OCRmyPDF pour les scans ;
- MinerU pour les tableaux, formules ou mises en page complexes ;
- reparation d'une copie de travail avec QPDF si necessaire.

La sortie de travail reste dans `/Users/insular/transcripts`. Chaque marqueur `[p. N]` correspond
au numero de page du PDF. Quand le numero imprime differe, il est conserve separement dans la
metadata `printed_page`.

### 4.3 Segmentation

Chaque livre est decoupe en chapitres ou blocs bornes. Chaque bloc contient :

- identifiant du livre ;
- edition ;
- chapitre ou section ;
- plage de pages ;
- empreinte du contenu ;
- chemin de la source de travail.

Un bloc trop long pour Gemini est subdivise sans perdre la plage de pages.

### 4.4 Extraction Gemini

Chaque livre deja reference utilise le prompt specialise de sa fiche. Pour Klarman, Lynch,
Grinold/Kahn et Annie Duke, une fiche `draft_to_validate` et un prompt specialise sont prepares
avant extraction. Le prompt demande uniquement :

- regles testables ;
- variables necessaires ;
- conditions ;
- action ou implication ;
- exceptions ;
- exemple chiffre si present ;
- limites ;
- citation chapitre et page.

Une sortie de type resume general est rejetee. Les reponses Gemini brutes sont conservees comme
artefacts de travail, separees des regles acceptees.

### 4.5 Validation documentaire

Chaque regle passe les controles suivants :

1. schema complet ;
2. citation presente ;
3. page existante dans le livre ;
4. passage source retrouvable ;
5. condition identifiable ;
6. conclusion fidele au passage ;
7. absence d'invention numerique ;
8. statut de confiance compatible avec le type de source.

Un echantillon de regles est relu manuellement a chaque iteration. Le pipeline n'est etendu au
livre complet que si cet echantillon atteint les criteres d'acceptation.

### 4.6 Consolidation

Les regles acceptees sont comparees aux connaissances courtes de Maxi Brain et aux regles deja
extraites.

La consolidation produit :

- convergences multi-sources ;
- doublons semantiques ;
- contradictions ;
- transpositions a verifier ;
- lacunes du corpus ;
- protocoles de validation quantitative a construire plus tard.

Elle ne produit aucune decision de trading.

## 5. Flux de donnees

```text
PDF original en lecture seule
  -> manifeste et diagnostic
  -> copie de travail dans transcripts
  -> extraction texte ou OCR
  -> Markdown pagine
  -> blocs par chapitre
  -> Gemini avec prompt specialise
  -> reponses brutes
  -> validation documentaire
  -> regles acceptees / rejetees / to_review
  -> deduplication et registre des contradictions
  -> base de recherche Take Two
```

## 6. Statuts

### Statut d'une source

- `ready_text`
- `needs_ocr`
- `needs_repair`
- `secondary_notes`
- `duplicate`
- `blocked`

### Statut d'une regle

- `extracted`
- `rejected_schema`
- `rejected_untraceable`
- `to_review`
- `documentary_validated`
- `conflict_open`
- `duplicate_merged`

`documentary_validated` signifie que la regle est fidele a la source. Cela ne signifie pas qu'elle
est vraie, rentable ou utilisable dans une strategie.

## 7. Gestion des erreurs

- Echec OCR : essayer le moteur suivant et enregistrer l'erreur.
- Page illisible : marquer la plage `to_review`, sans inventer le contenu.
- Reponse Gemini incomplete : relancer uniquement le bloc concerne.
- Citation introuvable : rejeter la regle.
- Doublon de PDF : traiter une seule copie et conserver les empreintes des alias.
- PDF endommage : reparer une copie de travail ; ne jamais modifier l'original.
- Limite API ou interruption : reprendre depuis le manifeste sans retraiter les blocs termines.

## 8. Iteration pilote

L'implementation commence sur de petits echantillons :

1. McMillan : un chapitre avec couche texte, pour calibrer le schema et le prompt.
2. Natenberg : dix pages scannees, pour calibrer l'OCR et la pagination.
3. Passarelli : dix pages avec tableaux ou exemples chiffres.
4. Controle croise avec une note courte pertinente de Maxi Brain.

Le traitement integral ne commence qu'apres validation de ces trois chemins.

## 9. Criteres d'acceptation du pilote

- 100 % des regles acceptees ont livre, chapitre et page.
- 100 % des pages citees existent et sont retrouvables.
- 0 seuil numerique accepte sans passage source.
- Au moins 90 % des citations d'un echantillon manuel soutiennent correctement la regle.
- Les reprises n'appellent pas Gemini une seconde fois pour un bloc deja termine.
- Les scans conservent une correspondance verifiable entre page PDF et marqueur Markdown.
- Les contradictions restent visibles.
- Aucun PDF, texte integral de livre ou secret Gemini n'apparait dans Git.

Si un critere echoue, le pilote est corrige et relance avant extension au corpus.

## 10. Sorties versionnees autorisees

Le repository peut versionner :

- manifeste sans contenu integral ;
- schemas ;
- prompts specialises ;
- regles atomiques avec citations courtes ;
- journaux de traitement sans secret ;
- registres de contradictions ;
- rapports de qualite ;
- specifications et tests.

Il ne versionne pas :

- PDF ;
- OCR integral ;
- Markdown integral des livres ;
- reponses contenant de longs extraits ;
- cle API ou fichier `.env`.

## 11. Hors perimetre de la phase 1

- conseil financier ;
- recommandation d'achat ou de vente ;
- classement d'options de marche ;
- donnees temps reel ;
- backtest de strategie ;
- Monte Carlo de portefeuille ;
- connexion ou ordre IBKR ;
- interface de trading ;
- automatisation d'execution.

Ces sujets ne pourront commencer qu'apres une decision explicite ouvrant une phase ulterieure.
