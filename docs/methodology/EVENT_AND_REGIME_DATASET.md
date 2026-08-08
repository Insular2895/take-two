# Dataset événements et régimes — phase I

Statut TTWO : `BLOCKED_MISSING_GOVERNED_EVENTS`.

Un événement conserve quatre temps distincts : événement, publication, disponibilité
et cutoff de décision. Une donnée disponible après le cutoff est exclue. La déduplication
utilise l'identifiant externe ; deux versions contradictoires restent visibles et bloquent
le dataset. Les rendements événementiels ne sont agrégés que si l'événement accepté et
l'horizon sont alignés.

Les régimes de tendance et volatilité sont déterministes et n'utilisent que les métriques
disponibles au cutoff. Leurs seuils restent `draft_to_validate` : ils constituent une
hypothèse, pas une décision. Le rapport réel est vide car aucune histoire d'événements
TTWO gouvernée, sourcée et point-in-time n'a été constituée dans le dépôt. Aucune ligne
SEC, earnings ou produit n'est inventée à partir de la mémoire courante.

Le holdout final reste fermé et le module est strictement read-only.
