# Roadmap données live

Cette roadmap ne constitue pas une autorisation d’activation. Aucune connexion live
n’est activée par défaut.

1. Paramétrer le socket local TWS/IB Gateway (`host`, `port`, `clientId`) sans clé API,
   puis valider compte, entitlements, licences, coûts et droits de redistribution.
2. Connecter un port read-only injecté : découverte contrats, spot, chaîne, timestamps,
   bid/ask, volume, open interest et Greeks.
3. Tester fraîcheur, trous, reconnexion, rate limits, cache, cutoff et fail-closed.
4. Nettoyer la surface, exclure les quotes invalides, contrôler l’arbitrage et journaliser
   les calibrations.
5. Récupérer les quotes combo et comparer la quote BAG au synthétique jambe par jambe.
6. Ajouter commissions et marge what-if à un preview expirant et non transmissible.
7. Passer par une campagne paper avant toute revue commerciale.

Point d'arrêt actuel : étape 1 paramétrée mais non confirmée, statut
`CONFIGURED_NOT_ENTITLED`, aucune connexion tentée.

Les fallbacks synthétiques sont interdits pour un résultat promu. Les détails
spécifiques au broker sont dans [IBKR_OPRA_ROADMAP.md](IBKR_OPRA_ROADMAP.md).
