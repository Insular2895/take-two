# Opérations et continuité avant restitution du Mac

## Objectif

Le Mac ne doit être ni l’unique copie du code, ni l’unique moyen d’administrer Oracle, Cloudflare,
GitHub ou IBKR.

## Checklist code

- [ ] tous les changements utiles sont commités ;
- [ ] la branche distante contient le dernier commit ;
- [ ] la fusion vers `main` est décidée et traçable ;
- [ ] un clone neuf passe les commandes de validation ;
- [ ] aucun `.env`, token, compte ou clé privée n’est suivi par Git ;
- [ ] le commit de handoff est noté dans ce dossier.

## Checklist accès

- [ ] clé SSH Oracle disponible sur le prochain appareil ou sauvegardée chiffrée ;
- [ ] permissions de la clé restaurables (`0600`) ;
- [ ] accès SSH réellement testé depuis l’autre appareil ;
- [ ] accès Cloudflare et GitHub testé avec 2FA ;
- [ ] identifiants IBKR et méthode 2FA récupérables sans le trousseau du Mac ;
- [ ] codes de récupération stockés hors du Mac ;
- [ ] procédure de rotation connue si le Mac n’est plus de confiance.

## Checklist Oracle

- [ ] IP/hostname et utilisateur connus sans exposer de secret dans Git ;
- [ ] UFW n’expose ni `4002` ni `5901` ;
- [ ] VNC passe seulement dans un tunnel SSH ;
- [ ] IB Gateway reste paper et Read-Only pour la validation data ;
- [ ] service systemd et fichier env root-only documentés ;
- [ ] logs ne contiennent ni compte, payload, URL signée ou secret ;
- [ ] procédure de réauthentification IB Gateway documentée.

## Sauvegarde des secrets

Ne pas copier les secrets dans le vault, Git, chat, capture d’écran ou documentation. Utiliser un
gestionnaire de mots de passe ou un support chiffré. Sauvegarder la capacité de rotation, pas
seulement la valeur actuelle.

## Tests après changement d’appareil

Le premier objectif n’est pas de connecter IBKR. Il faut d’abord : cloner, installer, lancer les
tests offline, accéder à Oracle, vérifier les services sans afficher leurs environnements, puis
seulement planifier la validation read-only.

