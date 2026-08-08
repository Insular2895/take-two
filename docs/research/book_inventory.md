# Inventaire documentaire TTWO — Phase 0

Statut : `draft_to_validate`

Date d'audit : 2026-08-08

Politique : sources PDF strictement `READ-ONLY`

## Résultat immédiat

Le chemin demandé `BOOK` n'existe ni dans le checkout, ni dans les arbres Git locaux inspectés. Le corpus a toutefois été retrouvé à `/Users/insular/Desktop/book 📙`. Ce chemin est un alias candidat de très forte confiance : il est déjà cité dans un ancien plan documentaire TTWO du vault et contient exactement les fragments Bergomi ainsi que les trois fichiers `interest rate` décrits dans le brief. Cet alias doit néanmoins être confirmé avant de devenir une convention du projet.

L'inventaire machine complet est dans [book_inventory.json](book_inventory.json). Il contient les 138 chemins récursifs observés. Aucun PDF n'a été déplacé, renommé, réparé ou modifié.

| Mesure | Résultat |
|---|---:|
| Fichiers récursifs | 138 |
| PDF avec extension `.pdf` | 136 |
| PDF sans extension | 1 |
| Fichiers non documentaires | 1 (`.DS_Store`) |
| Pages PDF lisibles | 32 983 |
| Charges utiles PDF uniques par SHA-256 | 133 |
| PDF `qpdf --check` propres | 76 |
| PDF lisibles avec avertissements structurels | 61 |
| PDF fatalement illisibles | 0 |
| Groupes de doublons binaires exacts | 3 |

Les 61 avertissements `qpdf` concernent surtout des tables d'indices ou offsets incohérents. Ils ne sont pas assimilés à une corruption de contenu : les 137 documents restent paginables. En revanche, une formule extraite d'un fichier averti ne pourra devenir une preuve quantitative qu'après contrôle par le pipeline de preuves PDF et, si nécessaire, revue visuelle/humaine.

## Œuvres fragmentées reconstruites

### Lorenzo Bergomi — *Stochastic Volatility Modeling*

Une seule œuvre, onze fichiers locaux. L'année et l'édition restent inconnues : elles ne sont pas déduites du nom du dossier. Les titres de chapitre ci-dessous ont été lus dans le texte des PDF.

| Fichier | Partie vérifiée | Pages locales |
|---|---|---:|
| `Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C3.pdf` | Ch. 3 — Forward-start options | 30 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C4.pdf` | Ch. 4 — Stochastic volatility – introduction | 18 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C5.pdf` | Ch. 5 — Variance swaps | 50 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C6.pdf` | Ch. 6 — An example of one-factor dynamics: the Heston model | 16 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C7.pdf` | Ch. 7 — Forward variance models | 90 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C8.pdf` | Ch. 8 — The smile of stochastic volatility models | 50 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C9.pdf` | Ch. 9 — Linking static and dynamic properties of stochastic volatility models | 34 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C10.pdf` | Ch. 10 — What causes equity smiles? | 30 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C11.pdf` | Ch. 11 — Multi-asset stochastic volatility | 32 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_C12.pdf` | Ch. 12 — Local-stochastic volatility models | 42 |
| `.../Bergomi_Lorenzo_Stochastic_Volatility_Modeling_ref.pdf` | Épilogue et fragment de références | 9 |

Le corpus est incomplet : les chapitres 1 et 2 ne sont pas présents. Une recherche Bergomi devra donc interroger tous les fragments et ne pourra pas conclure à l'absence d'un concept sur la seule base de ce corpus.

### Leif B.G. Andersen et Vladimir V. Piterbarg — *Interest Rate Modeling*

Une seule série documentaire, trois fichiers locaux. Le titre, les auteurs, la structure en trois volumes et la date 2010 ont été récupérés automatiquement dans la préface. L'édition n'est pas identifiable dans les fragments et reste `unknown`.

| Fichier | Reconstruction | Chapitres | Pages locales |
|---|---|---|---:|
| `interest rate/Interest_Rate_Modeling_by_Piterbarg_I-1.pdf` | Volume I — *Foundations and Vanilla Models*, fragment 1 | 1–5 | 247 |
| `interest rate/Interest_Rate_Modeling_by_Piterbarg_I-2.pdf` | Volume I — *Foundations and Vanilla Models*, fragment 2 | 6–9 | 172 |
| `interest rate/Interest_Rate_Modeling_by_Piterbarg_II.pdf` | Volume II — *Term Structure Models* | 10–15 | 288 |

Le Volume III — *Products and Risk Management* — est annoncé dans la table des matières générale mais absent du corpus. Les trois PDF présents ne sont donc ni trois livres indépendants, ni les trois volumes complets : deux fichiers reconstituent le Volume I et le troisième contient le Volume II.

Sections immédiatement pertinentes, sans décision d'implémentation :

- ch. 1 : mesures martingales, Black-Scholes et droits d'exercice anticipé ;
- ch. 2 : différences finies, stabilité et conditions aux limites ;
- ch. 3 : Monte Carlo, biais/erreur, antithétiques, contrôles et importance sampling ;
- ch. 4 : mesures de taux, HJM et numéraires ;
- ch. 6 : construction/interpolation de courbes et gestion du risque ;
- ch. 8–9 : volatilité stochastique, calibration et schémas Monte Carlo ;
- ch. 10–15 : taux courts, modèles multi-facteurs, HJM/LMM et calibration.

## Références prioritaires demandées

La présence signifie seulement que le fichier est disponible ; elle ne valide ni ses formules ni son édition.

| Référence demandée | Disponibilité locale | État bibliographique |
|---|---|---|
| Simmons — *Precalculus Mathematics in a Nutshell* | 2 fichiers candidats | titre/auteur visibles dans les noms ; versions à rapprocher |
| Stewart — *Calculus: Early Transcendentals* | présent | 9e édition métrique indiquée par le nom ; titre-page à confirmer avant citation |
| Strang — *Introduction to Linear Algebra* | présent | fichier candidat, édition inconnue |
| Blitzstein & Hwang — *Introduction to Probability* | présent | 2e édition/2019 indiqués par le nom ; métadonnées PDF pauvres |
| Zhou — *A Practical Guide to Quantitative Finance Interviews* | fichier candidat `practical guide finance interview.pdf` | identité à confirmer |
| Wasserman — *All of Statistics* | présent | année 2004 indiquée par le nom ; métadonnées PDF pauvres |
| McElreath — *Statistical Rethinking* | présent, plus un support candidat | 2e édition indiquée par le nom du livre |
| Särkkä — *Bayesian Filtering and Smoothing* | présent | seconde édition indiquée par le nom ; titre PDF vérifié |
| Süli & Mayers — *An Introduction to Numerical Analysis* | fichier candidat `Numerical_Analysis.pdf` | auteurs/édition à confirmer |
| Glasserman — *Monte Carlo Methods in Financial Engineering* | 2 fichiers candidats | même œuvre probable, payloads différents |
| Boyd & Vandenberghe — *Convex Optimization* | présent | identité de l'œuvre à confirmer sur titre-page |
| Nocedal & Wright — *Numerical Optimization* | présent | titre et auteurs vérifiés dans les métadonnées PDF |
| Tsay — *Analysis of Financial Time Series* | présent | 3e édition indiquée par le titre PDF |
| Shreve — *Stochastic Calculus for Finance II* | **absent** | seul le Volume I est présent |
| Björk — *Arbitrage Theory in Continuous Time* | présent | titre PDF vérifié ; édition à confirmer |
| Gatheral — *The Volatility Surface* | **absent** | source primaire SVI à obtenir avant Phase 2 |
| Bergomi — *Stochastic Volatility Modeling* | présent, fragmenté | ch. 3–12 + épilogue ; année/édition inconnues |
| Andersen & Piterbarg — *Interest Rate Modeling* | présent, fragmenté | Vol. I–II partiels ; 2010 vérifié ; édition inconnue |

## Doublons

Doublons binaires prouvés par SHA-256 :

- `MOD_free_chapter.pdf` et `MOD_free_chapter (1).pdf` ;
- les trois fichiers `Trading in the Zone - Mark Douglas (2001) A202...` ;
- les deux fichiers `.pdf` `option-volatility-and-pricing-sheldon-natenberg...`.

Doublons bibliographiques probables mais non prouvés comme éditions identiques : les deux Glasserman, les deux `Currency Strategy`, et le fichier Natenberg sans extension comparé aux deux copies `.pdf`. Ils restent `to_review`.

## Summarizer et « Transcript » : syntaxe réelle

Les exécutables ne sont pas installés dans le `PATH`. Le projet local est `/Users/insular/transcripts` et doit être invoqué depuis cette racine.

```bash
cd /Users/insular/transcripts
./runhelp
./summarizer
./runpdf "/chemin/vers/livre.pdf"
./runpdf "/chemin/vers/livre.pdf" --engine smart --overwrite
./runpdf "/chemin/vers/livre.pdf" --instruction "question ciblée"
./runpdf "/chemin/vers/livre.pdf" --max-pages 10 --overwrite
./.venv/bin/python -m src.cli run-pdf "/chemin/vers/livre.pdf" \
  --no-visual-review --overwrite
./pdf-evidence inspect "/chemin/vers/livre.pdf" --pdf-page 132 \
  --element-id p000132-table-7-2 --dpi 450 --include-context --open-images
./pdf-evidence regression --output cache/pdf_evidence_golden/regression-report.json
```

`./runyoutube` produit et conserve des transcriptions vidéo. Aucun binaire, script ou application autonome nommé `Transcript`, `transcript` ou `transcribe` n'a été trouvé dans le dépôt, dans le `PATH`, ni lors de la recherche locale bornée. La capacité appelée « Transcript » dans le brief correspond donc vraisemblablement au pipeline de transcription du projet Summarizer ; cette correspondance reste une hypothèse à valider.

Le pipeline PDF garantit une source en lecture seule, calcule son SHA-256, sépare page PDF/page imprimée et écrit des sidecars de preuve. Une sortie de résumé seule n'est pas une preuve. Une valeur quantitative ambiguë doit rester `needs_visual_review`, `human_review_required` ou `blocked`; elle ne peut être promue que par une revue explicite.

## Méthode et reproductibilité

La Phase 0 a utilisé `find`, `file`, `mdls`, `qpdf --show-npages`, `qpdf --check`, SHA-256, extraction texte Ghostscript et OCR Tesseract ciblé. Aucun job Summarizer complet n'a été lancé : la recherche formule/section est réservée à la `Documentary Research` précédant chaque phase quantitative.

Limites :

- l'alias du chemin `BOOK` doit être confirmé ;
- le nombre d'œuvres bibliographiques uniques reste volontairement `unknown` malgré 133 payloads uniques ;
- 61 PDF imposent une vigilance d'extraction ;
- Gatheral et Shreve II manquent pour deux chantiers prioritaires ;
- aucune page ni édition n'a été complétée à partir d'une supposition.
