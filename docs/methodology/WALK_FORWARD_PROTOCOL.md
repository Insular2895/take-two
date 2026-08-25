# Walk-forward, purge et embargo — phase E

Le protocole suit strictement : passé → calibration → gel → prédiction validation →
observation → prédiction test → score → avance.

Le run de diagnostic actuel utilise une fenêtre d'entraînement croissante, 252
observations minimales, 5 observations purgées, 40 observations de validation, 5
observations d'embargo et 40 observations de test. Il produit sept fenêtres. Une
configuration `rolling` utilise le même moteur avec une longueur d'entraînement fixe.

Chaque manifeste de fenêtre enregistre les bornes temporelles, hashes dataset/config,
paramètres et hash du modèle gelé, IDs purgés et embargo, résumés des prédictions et
résultats réalisés. Les enregistrements journaliers exacts restent privés à cause de la
licence ; leur hash permet de vérifier le run local sans redistribuer la série.

Le modèle gaussien historique est un témoin de protocole, pas « V10 ». Ses probabilités
de profit proches de 51–52 % et ses Brier scores proches de 0,25 n'établissent aucun
edge. La phase G devra comparer les candidats et baselines sur des conventions
identiques. Aucun résultat de phase E n'a accès au holdout final.

Les limites actuelles sont structurelles : licence `to_review`, séries options non
transformées en trajectoires de stratégies et fenêtres déjà exposées au développement.
Le statut reste donc `DIAGNOSTIC_ONLY_LICENSE_REVIEW`.
